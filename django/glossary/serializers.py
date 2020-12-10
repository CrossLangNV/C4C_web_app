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
        concept_offsets_json_dict = {"concept_id":validated_data["concept"].id, "document_id":validated_data["document"].id, "probability":"1", "begin":validated_data["startOffset"], "end":validated_data["endOffset"]}
        if (validated_data["annotation_type"] == "occurence"):
            concept_occurs = ConceptOccurs.objects.create(**concept_offsets_json_dict)
            validated_data["concept_occurs"] = concept_occurs
            validated_data["concept_defined"] = None
        elif (validated_data["annotation_type"] == "definition"):
            concept_defined = ConceptDefined.objects.create(**concept_offsets_json_dict)
            validated_data["concept_defined"] = concept_defined
            validated_data["concept_occurs"] = None
        
        annotation_worklog = AnnotationWorklog.objects.create(**validated_data)
        print(annotation_worklog.concept_occurs)
        print(annotation_worklog.concept_defined)
        return annotation_worklog

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ['password']


class AcceptanceStateSerializer(serializers.ModelSerializer):
    concept = serializers.PrimaryKeyRelatedField(
        queryset=Concept.objects.all())
    user = UserSerializer(read_only=True)

    class Meta:
        model = AcceptanceState
        fields = '__all__'


class ConceptSerializer(serializers.ModelSerializer):
    comments = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    acceptance_states = AcceptanceStateSerializer(many=True, read_only=True)
    acceptance_state = serializers.SerializerMethodField()
    acceptance_state_value = serializers.SerializerMethodField()

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
        fields = ('id','name','definition')

class CommentSerializer(serializers.ModelSerializer):
    Concept = serializers.PrimaryKeyRelatedField(
        queryset=Concept.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Comment
        fields = '__all__'