from django.contrib.auth.models import User
from rest_framework import serializers

from searchapp.models import Attachment, Document, Website, AcceptanceState, Comment, Tag

import logging

logger = logging.getLogger(__name__)


class WebsiteSerializer(serializers.ModelSerializer):
    documents = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Website
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class DocumentSerializer(serializers.ModelSerializer):
    website = serializers.PrimaryKeyRelatedField(
        queryset=Website.objects.all())
    attachments = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    comments = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    acceptance_state = serializers.SerializerMethodField()
    acceptance_state_value = serializers.SerializerMethodField()

    def get_acceptance_state(self, document):
        user = self.context['request'].user
        qs = AcceptanceState.objects.filter(document=document, user=user)
        serializer = AcceptanceStateSerializer(instance=qs, many=True)
        state_id = None
        if len(serializer.data) > 0:
            state_id = serializer.data[0]['id']
        else:
            new_unvalidated_state = AcceptanceState.objects.create(
                document=document,
                user=user
            )
            state_id = new_unvalidated_state.id
        return state_id

    def get_acceptance_state_value(self, document):
        user = self.context['request'].user
        qs = AcceptanceState.objects.filter(document=document, user=user)
        return qs.values_list('value', flat=True)[0]

    class Meta:
        model = Document
        fields = '__all__'


class AcceptanceStateSerializer(serializers.ModelSerializer):
    document = serializers.PrimaryKeyRelatedField(
        queryset=Document.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = AcceptanceState
        fields = '__all__'


class AttachmentSerializer(serializers.ModelSerializer):
    document = serializers.PrimaryKeyRelatedField(
        queryset=Document.objects.all())

    class Meta:
        model = Attachment
        fields = '__all__'


class CommentSerializer(serializers.ModelSerializer):
    document = serializers.PrimaryKeyRelatedField(
        queryset=Document.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Comment
        fields = '__all__'
