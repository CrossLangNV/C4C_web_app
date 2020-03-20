from django.contrib.auth.models import User
from rest_framework import serializers

from searchapp.models import Attachment, Document, Website, AcceptanceState


class WebsiteSerializer(serializers.ModelSerializer):
    documents = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Website
        fields = '__all__'


class DocumentSerializer(serializers.ModelSerializer):
    website = serializers.PrimaryKeyRelatedField(queryset=Website.objects.all())
    attachments = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    acceptance_state = serializers.SerializerMethodField()

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

    class Meta:
        model = Document
        fields = '__all__'


class AcceptanceStateSerializer(serializers.ModelSerializer):
    document = serializers.PrimaryKeyRelatedField(queryset=Document.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = AcceptanceState
        fields = '__all__'


class AttachmentSerializer(serializers.ModelSerializer):
    document = serializers.PrimaryKeyRelatedField(queryset=Document.objects.all())

    class Meta:
        model = Attachment
        fields = '__all__'
