from flask import Flask, jsonify, request
import aiohttp
import asyncio
import json
import sys
import os

# Vercel এ protobuf issue fix - dynamic loading
try:
    from visit_count_pb2 import Info
except Exception as e:
    print(f"⚠️ Protobuf import error, using fallback: {e}")
    from google.protobuf import message_factory
    from google.protobuf import descriptor_pb2
    
    DESCRIPTOR = descriptor_pb2.FileDescriptorProto(
        name='visit_count.proto',
        package='proto',
        message_type=[
            descriptor_pb2.DescriptorProto(
                name='BasicInfo',
                field=[
                    descriptor_pb2.FieldDescriptorProto(
                        name='UID',
                        number=1,
                        type=descriptor_pb2.FieldDescriptorProto.TYPE_INT64,
                        label=descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
                    ),
                    descriptor_pb2.FieldDescriptorProto(
                        name='PlayerNickname',
                        number=3,
                        type=descriptor_pb2.FieldDescriptorProto.TYPE_STRING,
                        label=descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
                    ),
                    descriptor_pb2.FieldDescriptorProto(
                        name='PlayerRegion',
                        number=5,
                        type=descriptor_pb2.FieldDescriptorProto.TYPE_STRING,
                        label=descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
                    ),
                    descriptor_pb2.FieldDescriptorProto(
                        name='Levels',
                        number=6,
                        type=descriptor_pb2.FieldDescriptorProto.TYPE_INT64,
                        label=descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
                    ),
                    descriptor_pb2.FieldDescriptorProto(
                        name='Likes',
                        number=21,
                        type=descriptor_pb2.FieldDescriptorProto.TYPE_INT64,
                        label=descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
                    ),
                ]
            ),
            descriptor_pb2.DescriptorProto(
                name='Info',
                field=[
                    descriptor_pb2.FieldDescriptorProto(
                        name='AccountInfo',
                        number=1,
                        type=descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE,
                        label=descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL,
                        type_name='.proto.BasicInfo'
                    ),
                ]
            )
        ]
    )
    
    _factory = message_factory.MessageFactory()
    BasicInfo = _factory.GetPrototype(_factory.GetDescriptor('proto.BasicInfo', DESCRIPTOR))
    Info = _factory.GetPrototype(_factory.GetDescriptor('proto.Info', DESCRIPTOR))

app = Flask(__name__)

def load_tokens(server_name):
    try:
        if server_name == "IND":
            path = "token_ind.json"
        elif server_name in {"BR", "US", "SAC", "NA"}:
            path = "token_br.json"
        else:
            path = "token_bd.json"

        with open(path, "r", encoding='utf-8') as f:
            data = json.load(f)

        tokens = []
        for item in data:
            if "token" in item and item["token"] not in ["", "N/A"]:
                tokens.append(item["token"])
        
        print(f"✅ Loaded {len(tokens)} tokens from {path}")
        return tokens
    except Exception as e:
        print(f"❌ Token load error: {e}")
        return []

def get_url(server_name):
    if server_name == "IND":
        return "https://client.ind.freefiremobile.com/GetPlayerPersonalShow"
    elif server_name in {"BR", "US", "SAC", "NA"}:
        return "https://client.us.freefiremobile.com/GetPlayerPersonalShow"
    else:
        return "https://clientbp.ggblueshark.com/GetPlayerPersonalShow"

def parse_protobuf_response(response_data):
    try:
        info = Info()
        info.ParseFromString(response_data)
        
        player_data = {
            "uid": info.AccountInfo.UID if info.AccountInfo.UID else 0,
            "nickname": info.AccountInfo.PlayerNickname if info.AccountInfo.PlayerNickname else "",
            "likes": info.AccountInfo.Likes if info.AccountInfo.Likes else 0,
            "region": info.AccountInfo.PlayerRegion if info.AccountInfo.PlayerRegion else "",
            "level": info.AccountInfo.Levels if info.AccountInfo.Levels else 0
        }
        return player_data
    except Exception as e:
        print(f"❌ Protobuf parsing error: {e}")
        return None

async def visit(session, url, token, uid, data):
    headers = {
        "ReleaseVersion": "OB54",
        "X-GA": "v1 1",
        "Authorization": f"Bearer {token}",
        "Host": url.replace("https://", "").split("/")[0]
    }
    try:
        async with session.post(url, headers=headers, data=data, ssl=False) as resp:
            if resp.status == 200:
                response_data = await resp.read()
                return True, response_data
            else:
                return False, None
    except Exception as e:
        print(f"❌ Visit error: {e}")
        return False, None

async def send_until_1000_success(tokens, uid, server_name, target_success=1000):
    url = get_url(server_name)
    connector = aiohttp.TCPConnector(limit=0)
    total_success = 0
    total_sent = 0
    first_success_response = None
    player_info = None

    async with aiohttp.ClientSession(connector=connector) as session:
        try:
            from byte import encrypt_api, Encrypt_ID
            encrypted = encrypt_api("08" + Encrypt_ID(str(uid)) + "1801")
            data = bytes.fromhex(encrypted)
        except Exception as e:
            print(f"❌ Encryption error: {e}")
            return 0, 0, None

        while total_success < target_success:
            batch_size = min(target_success - total_success, 300)
            tasks = [
                asyncio.create_task(visit(session, url, tokens[(total_sent + i) % len(tokens)], uid, data))
                for i in range(batch_size)
            ]
            results = await asyncio.gather(*tasks)
            
            if first_success_response is None:
                for success, response in results:
                    if success and response is not None:
                        first_success_response = response
                        player_info = parse_protobuf_response(response)
                        break
            
            batch_success = sum(1 for r, _ in results if r)
            total_success += batch_success
            total_sent += batch_size

            print(f"Batch sent: {batch_size}, Success in batch: {batch_success}, Total success so far: {total_success}")

    return total_success, total_sent, player_info

@app.route('/visit', methods=['GET'])
def send_visits():
    uid = request.args.get('uid')
    server = request.args.get('server_name')
    
    if not uid:
        return jsonify({"error": "❌ uid parameter is required"}), 400
    if not server:
        return jsonify({"error": "❌ server_name parameter is required"}), 400
    
    try:
        uid = int(uid)
    except ValueError:
        return jsonify({"error": "❌ uid must be an integer"}), 400
    
    server = server.upper()
    tokens = load_tokens(server)
    target_success = 1000

    if not tokens:
        return jsonify({"error": f"❌ No valid tokens found for {server}"}), 500

    print(f"🚀 Sending visits to UID: {uid} using {len(tokens)} tokens")
    print(f"Waiting for total {target_success} successful visits...")

    total_success, total_sent, player_info = asyncio.run(send_until_1000_success(
        tokens, uid, server,
        target_success=target_success
    ))

    if player_info:
        player_info_response = {
            "fail": target_success - total_success,
            "level": player_info.get("level", 0),
            "likes": player_info.get("likes", 0),
            "nickname": player_info.get("nickname", ""),
            "region": player_info.get("region", ""),
            "success": total_success,
            "uid": player_info.get("uid", 0)
        }
        return jsonify(player_info_response), 200
    else:
        return jsonify({"error": "Could not decode player information"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)