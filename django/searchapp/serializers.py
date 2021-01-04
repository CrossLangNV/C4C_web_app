from django.contrib.auth.models import User
from rest_framework import serializers

from searchapp.models import Attachment, Document, Website, AcceptanceState, Comment, Tag, Bookmark
from glossary.serializers import ConceptDocumentSerializer

import logging
import os

logger = logging.getLogger(__name__)
EXTRACT_TERMS_NLP_VERSION = os.environ.get(
    'EXTRACT_TERMS_NLP_VERSION', '8a4f1d58')


class WebsiteSerializer(serializers.ModelSerializer):
    total_documents = serializers.IntegerField(read_only=True)

    class Meta:
        model = Website
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ['password']


class AcceptanceStateSerializer(serializers.ModelSerializer):
    document = serializers.PrimaryKeyRelatedField(
        queryset=Document.objects.all())
    user = UserSerializer(read_only=True)

    class Meta:
        model = AcceptanceState
        fields = '__all__'


class AttachmentWithoutContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        exclude = ['content', 'file']


class DocumentSerializer(serializers.ModelSerializer):
    website = serializers.PrimaryKeyRelatedField(
        queryset=Website.objects.all())
    website_name = serializers.SerializerMethodField()
    attachments = AttachmentWithoutContentSerializer(many=True, read_only=True)
    comments = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    acceptance_states = AcceptanceStateSerializer(many=True, read_only=True)
    acceptance_state = serializers.SerializerMethodField()
    acceptance_state_value = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()
    bookmark = serializers.SerializerMethodField()
    definition = serializers.SerializerMethodField()

    def get_definition(self, document):
        qs = document.definition.filter(version=EXTRACT_TERMS_NLP_VERSION)
        serializer = ConceptDocumentSerializer(
            instance=qs, many=True, read_only=True)
        return serializer.data

    def get_content(self, document):
        try:
            return document.content.strip()
        except AttributeError:
            return ""

    def get_bookmark(self, document):
        user = self.context['request'].user
        if len(document.bookmarks.filter(user=user)) > 0:
            return True
        else:
            return False

    def get_acceptance_state(self, document):
        user = self.context['request'].user
        qs = AcceptanceState.objects.filter(document=document, user=user)
        serializer = AcceptanceStateSerializer(instance=qs, many=True)
        state_id = None
        if len(serializer.data) > 0:
            state_id = serializer.data[0]['id']
        return state_id

    def get_acceptance_state_value(self, document):
        user = self.context['request'].user
        qs = AcceptanceState.objects.filter(document=document, user=user)
        res = qs.values_list('value', flat=True)
        if len(res):
            return res[0]
        else:
            return None

    def get_website_name(self, document):
        return document.website.name

    class Meta:
        model = Document
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


class BookmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bookmark
        fields = ['document']
