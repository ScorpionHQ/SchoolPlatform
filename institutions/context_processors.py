def tenant_context(request):
    return {
        "current_institution": getattr(
            request,
            "current_institution",
            None,
        ),
        "user_institutions": getattr(
            request,
            "user_institutions",
            None,
        ),
    }
