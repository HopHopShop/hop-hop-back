from rest_framework import serializers

from contact_us.models import Contact


class ContactUsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = '__all__'

        read_only_fields = ('id',)
        write_only_fields = ('created_at',)
