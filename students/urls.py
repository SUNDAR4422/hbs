from django.urls import path
from .views import (
    StudentProfileView, DepartmentListView,
    BulkStudentUploadView, StudentListView,
    StudentDetailView, StudentCreateView,
    DepartmentManageView, DepartmentDetailView,
    AcademicYearView
)

urlpatterns = [
    path('profile/', StudentProfileView.as_view(), name='student_profile'),
    path('departments/', DepartmentListView.as_view(), name='departments'),
    path('departments/manage/', DepartmentManageView.as_view(), name='department_manage'),
    path('departments/<int:pk>/', DepartmentDetailView.as_view(), name='department_detail'),
    path('academic-year/', AcademicYearView.as_view(), name='academic_year'),
    path('bulk-upload/', BulkStudentUploadView.as_view(), name='bulk_upload'),
    path('list/', StudentListView.as_view(), name='student_list'),
    path('create/', StudentCreateView.as_view(), name='student_create'),
    path('<int:pk>/', StudentDetailView.as_view(), name='student_detail'),
]
