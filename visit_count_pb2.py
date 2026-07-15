# -*- coding: utf-8 -*-
from google.protobuf import descriptor_pb2
from google.protobuf import message_factory

try:
    from google.protobuf.pyext import _message
except ImportError:
    _message = None

DESCRIPTOR = descriptor_pb2.FileDescriptorProto(
    name='visit_count.proto',
    package='proto',
    dependency=[],
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

# Build message classes
_factory = message_factory.MessageFactory()
BasicInfo = _factory.GetPrototype(
    _factory.GetDescriptor('proto.BasicInfo', DESCRIPTOR)
)
Info = _factory.GetPrototype(
    _factory.GetDescriptor('proto.Info', DESCRIPTOR)
)