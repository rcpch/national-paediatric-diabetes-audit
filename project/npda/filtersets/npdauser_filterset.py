from django.db.models import Q
from django.forms import TextInput
from django_filters import CharFilter, FilterSet

from project.npda.models import NPDAUser


class NPDAUserFilterSet(FilterSet):
    search = CharFilter(
        method="filter_search",
        widget=TextInput(
            attrs={
                "placeholder": "Search by email, first name, surname, PDU (PZ code or lead organisation name) or Network (PN Code or name)...",
                "class": "form-control text-center placeholder-gray-300 focus:bg-rcpch_strong_blue_light_tint2 hover:bg-rcpch_strong_blue_light_tint2 focus:placeholder-gray-500 p-2 m-2 w-full",
            }
        ),
        label="Search users",
    )

    class Meta:
        model = NPDAUser
        fields = []

    def filter_search(self, queryset, name, value):
        if value:
            queryset = queryset.filter(
                Q(pk__icontains=value)
                | Q(email__icontains=value)
                | Q(first_name__icontains=value)
                | Q(surname__icontains=value)
                | Q(organisation_employers__pz_code__icontains=value)
                | Q(organisation_employers__lead_organisation_name__icontains=value)
                | Q(
                    organisation_employers__paediatric_diabetes_network_code__icontains=value
                )
                | Q(
                    organisation_employers__paediatric_diabetes_network_name__icontains=value
                )
            )
        return queryset
