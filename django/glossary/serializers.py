from rest_framework import serializers
from django.contrib.auth.models import User

from glossary.models import Concept, Comment, Tag, AcceptanceState, AnnotationWorklog, ConceptOccurs, ConceptDefined


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class AnnotationWorklogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnnotationWorklog
        fields = '__all__'

    def create(self, validated_data):
        annotation_worklog = AnnotationWorklog.objects.create(**validated_data)
        return annotation_worklog

class ConceptOccursSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConceptOccurs
        fields = '__all__'

    def create(self, validated_data):
        concept_occurs = ConceptOccurs.objects.create(**validated_data)
        return concept_occurs

class ConceptDefinedSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConceptDefined
        fields = '__all__'

    def create(self, validated_data):
        concept_defined = ConceptDefined.objects.create(**validated_data)
        return concept_defined

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']


class AcceptanceStateSerializer(serializers.ModelSerializer):
    concept = serializers.PrimaryKeyRelatedField(
        queryset=Concept.objects.all())
    user = UserSerializer(read_only=True)

    class Meta:
        model = AcceptanceState
        fields = '__all__'


class ConceptOtherSerializer(serializers.ModelSerializer):

    class Meta:
        model = Concept
        fields = ['id', 'name']


class ConceptSerializer(serializers.ModelSerializer):
    comments = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    acceptance_states = AcceptanceStateSerializer(many=True, read_only=True)
    acceptance_state = serializers.SerializerMethodField()
    acceptance_state_value = serializers.SerializerMethodField()
    other = ConceptOtherSerializer(many=True, read_only=True)

    def get_acceptance_state(self, concept):
        user = self.context['request'].user
        qs = AcceptanceState.objects.filter(concept=concept, user=user)
        serializer = AcceptanceStateSerializer(instance=qs, many=True)
        state_id = None
        if len(serializer.data) > 0:
            state_id = serializer.data[0]['id']
        else:
            new_unvalidated_state = AcceptanceState.objects.create(
                concept=concept,
                user=user
            )
            state_id = new_unvalidated_state.id
        return state_id

    def get_acceptance_state_value(self, concept):
        user = self.context['request'].user
        qs = AcceptanceState.objects.filter(concept=concept, user=user)
        res = qs.values_list('value', flat=True)
        if len(res):
            return res[0]
        else:
            return None

    class Meta:
        model = Concept
        fields = '__all__'


class ConceptDocumentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Concept
        fields = ('id', 'name', 'definition')


class CommentSerializer(serializers.ModelSerializer):
    Concept = serializers.PrimaryKeyRelatedField(
        queryset=Concept.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Comment
        fields = '__all__'
