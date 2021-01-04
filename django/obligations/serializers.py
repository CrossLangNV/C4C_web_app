from rest_framework import serializers

from obligations.models import ReportingObligation, Tag, AcceptanceState, Comment
from django.contrib.auth.models import User
import logging as logger


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ['password']


class AcceptanceStateSerializer(serializers.ModelSerializer):
    reporting_obligation = serializers.PrimaryKeyRelatedField(
        queryset=ReportingObligation.objects.all())
    user = UserSerializer(read_only=True)

    class Meta:
        model = AcceptanceState
        fields = '__all__'


class CommentSerializer(serializers.ModelSerializer):
    reporting_obligation = serializers.PrimaryKeyRelatedField(
        queryset=ReportingObligation.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Comment
        fields = '__all__'


class ReportingObligationSerializer(serializers.ModelSerializer):
    comments = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    acceptance_states = AcceptanceStateSerializer(many=True, read_only=True)
    acceptance_state = serializers.SerializerMethodField()
    acceptance_state_value = serializers.SerializerMethodField()

    def get_acceptance_state(self, reporting_obligation):
        user = self.context['request'].user
        qs = AcceptanceState.objects.filter(reporting_obligation=reporting_obligation, user=user)
        serializer = AcceptanceStateSerializer(instance=qs, many=True)
        state_id = None
        if len(serializer.data) > 0:
            state_id = serializer.data[0]['id']
        else:
            new_unvalidated_state = AcceptanceState.objects.create(
                reporting_obligation=reporting_obligation,
                user=user
            )
            state_id = new_unvalidated_state.id
        return state_id

    def get_acceptance_state_value(self, reporting_obligation):
        user = self.context['request'].user
        qs = AcceptanceState.objects.filter(reporting_obligation=reporting_obligation, user=user)
        res = qs.values_list('value', flat=True)
        if len(res):
            return res[0]
        else:
            return None

    class Meta:
        model = ReportingObligation
        fields = '__all__'
