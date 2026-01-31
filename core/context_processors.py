from .models import Cart, UserProfile


def user_role(request):
    role = None
    if request.user.is_authenticated:
        try:
            role = request.user.userprofile.role
        except UserProfile.DoesNotExist:
            role = None

    cart_count = 0
    if request.user.is_authenticated:
        cart = (
            Cart.objects.filter(user=request.user, is_active=True)
            .prefetch_related('items')
            .first()
        )
        if cart:
            cart_count = cart.total_items()

    return {
        'current_role': role,
        'cart_item_count': cart_count,
    }

