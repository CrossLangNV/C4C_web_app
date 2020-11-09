from rest_framework import serializers

from obligations.models import ReportingObligation


class ReportingObligationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportingObligation
        fields = '__all__'


