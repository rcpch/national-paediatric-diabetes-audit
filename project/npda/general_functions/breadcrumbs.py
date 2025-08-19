from django.urls import reverse

from ..templatetags.npda_tags import format_nhs_number


def data_breadcrumbs(pdu, audit_period, entries):
    return [
        {
            "label": label,
            "href": reverse(viewname, kwargs={
                "pz_code": pdu.pz_code,
                "audit_period": audit_period.slug
            })
        } for (label, viewname) in entries
    ]

def patient_breadcrumbs(pdu, audit_period, patient, entries):
    return data_breadcrumbs(pdu, audit_period, [
            ("Patient Data", "pdu-patients"),
    ]) + [
        {
            "label": patient.unique_reference_number or format_nhs_number(patient.nhs_number),
            "href": reverse("pdu-patient-update", kwargs={
                "pz_code": pdu.pz_code,
                "audit_period": audit_period.slug,
                "pk": patient.pk
            })
        }
    ] + entries