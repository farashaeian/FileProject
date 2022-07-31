from rest_framework import permissions


class LoggedInUserPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.id == request.parser_context['kwargs']['pk']:
            return True
