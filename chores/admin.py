from django.contrib import admin
from .models import Parent, Child, Chore, ComputerTime, Reward, PointTransaction, ChoreAssignment

@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email')
    search_fields = ('first_name', 'last_name', 'email')

@admin.register(Child)
class ChildAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'user')
    list_filter = ('parent',)
    search_fields = ('name',)

@admin.register(Chore)
class ChoreAdmin(admin.ModelAdmin):
    # Changed 'points' to 'base_points' to match your models.py
    list_display = ('name', 'category', 'base_points')
    list_filter = ('category',)
    search_fields = ('name',)

# @admin.register(ToDoItem)
# class ToDoItemAdmin(admin.ModelAdmin):
#     # 'task' and 'priority' are valid fields in your ToDoItem model
#     list_display = ('task', 'child', 'due_date', 'priority', 'completed')
#     list_filter = ('completed', 'priority', 'due_date')
#     search_fields = ('task',)

@admin.register(ComputerTime)
class ComputerTimeAdmin(admin.ModelAdmin):
    list_display = ('child', 'date', 'minutes_allowed', 'minutes_used')
    list_filter = ('date', 'child')

@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
    list_display = ('name', 'point_cost', 'stock', 'is_available')
    list_filter = ('is_available',)

@admin.register(PointTransaction)
class PointTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'transaction_type', 'timestamp')
    list_filter = ('transaction_type', 'timestamp')


@admin.register(ChoreAssignment)
class ChoreAssignmentAdmin(admin.ModelAdmin):
    list_display = ('chore','assigned_to','due_date', 'status', 'completed_at')
    list_filter = ('chore', 'status',)


