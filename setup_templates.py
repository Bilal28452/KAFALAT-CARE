"""
KafalatCare Template Structure Setup Script
=============================================

This script creates all necessary template files for the KafalatCare application.
Run this from the project root: python setup_templates.py

The script will create the following structure:
- children/templates/children/
  - child_form.html
  - child_list.html
  - child_detail.html
  - child_confirm_delete.html
  - health_record_form.html
  - health_record_list.html
  - health_record_detail.html
  - health_record_confirm_delete.html
  - education_record_form.html
  - education_record_list.html
  - education_record_detail.html
  - education_record_confirm_delete.html

- sponsorships/templates/sponsorships/
  - sponsorship_form.html
  - sponsorship_list.html
  - sponsorship_detail.html
  - sponsorship_confirm_delete.html

- staff_management/templates/staff_management/
  - staff_form.html
  - staff_list.html
  - staff_detail.html
  - staff_confirm_delete.html

- donations/templates/donations/
  - donation_form.html
  - donation_list.html
  - donation_detail.html
  - donation_confirm_delete.html
"""

import os
from pathlib import Path

TEMPLATES = {
    # Children Templates
    'children/templates/children/child_form.html': '''{% extends "core/base.html" %}

{% block title %}{% if action == 'Create' %}Add Child{% else %}Edit Child{% endif %} - KafalatCare{% endblock %}

{% block content %}
<div class="container py-4">
  <div class="d-flex align-items-center justify-content-between mb-4">
    <div>
      <h1 class="h2">{{ action }} Child Record</h1>
      <p class="text-muted">Fill in the form to {% if action == 'Create' %}add a new child{% else %}update child information{% endif %}</p>
    </div>
    <a href="{% url 'child_list' %}" class="btn btn-outline-secondary">
      <i class="bi bi-arrow-left"></i> Back to List
    </a>
  </div>

  <div class="row">
    <div class="col-lg-8">
      <div class="card shadow-sm">
        <div class="card-body">
          <form method="post" novalidate>
            {% csrf_token %}

            <div class="mb-4">
              <h5 class="card-title mb-3">Basic Information</h5>
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label class="form-label">{{ form.child_id.label }}</label>
                  {{ form.child_id }}
                  {% if form.child_id.errors %}<div class="invalid-feedback d-block">{{ form.child_id.errors.0 }}</div>{% endif %}
                </div>
                <div class="col-md-6 mb-3">
                  <label class="form-label">{{ form.full_name.label }}</label>
                  {{ form.full_name }}
                  {% if form.full_name.errors %}<div class="invalid-feedback d-block">{{ form.full_name.errors.0 }}</div>{% endif %}
                </div>
              </div>

              <div class="row">
                <div class="col-md-6 mb-3">
                  <label class="form-label">{{ form.date_of_birth.label }}</label>
                  {{ form.date_of_birth }}
                  {% if form.date_of_birth.errors %}<div class="invalid-feedback d-block">{{ form.date_of_birth.errors.0 }}</div>{% endif %}
                </div>
                <div class="col-md-6 mb-3">
                  <label class="form-label">{{ form.gender.label }}</label>
                  {{ form.gender }}
                  {% if form.gender.errors %}<div class="invalid-feedback d-block">{{ form.gender.errors.0 }}</div>{% endif %}
                </div>
              </div>
            </div>

            <hr class="my-4">

            <div class="mb-4">
              <h5 class="card-title mb-3">Health & Status</h5>
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label class="form-label">{{ form.health_status.label }}</label>
                  {{ form.health_status }}
                  {% if form.health_status.errors %}<div class="invalid-feedback d-block">{{ form.health_status.errors.0 }}</div>{% endif %}
                </div>
                <div class="col-md-6 mb-3">
                  <label class="form-label">{{ form.sponsor_status.label }}</label>
                  {{ form.sponsor_status }}
                  {% if form.sponsor_status.errors %}<div class="invalid-feedback d-block">{{ form.sponsor_status.errors.0 }}</div>{% endif %}
                </div>
              </div>
            </div>

            <hr class="my-4">

            <div class="mb-4">
              <h5 class="card-title mb-3">Education & Contact</h5>
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label class="form-label">{{ form.education_level.label }}</label>
                  {{ form.education_level }}
                  {% if form.education_level.errors %}<div class="invalid-feedback d-block">{{ form.education_level.errors.0 }}</div>{% endif %}
                </div>
                <div class="col-md-6 mb-3">
                  <label class="form-label">{{ form.emergency_contact.label }}</label>
                  {{ form.emergency_contact }}
                  {% if form.emergency_contact.errors %}<div class="invalid-feedback d-block">{{ form.emergency_contact.errors.0 }}</div>{% endif %}
                </div>
              </div>
            </div>

            <hr class="my-4">

            <div class="mb-4">
              <h5 class="card-title mb-3">Admission</h5>
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label class="form-label">{{ form.admission_date.label }}</label>
                  {{ form.admission_date }}
                  {% if form.admission_date.errors %}<div class="invalid-feedback d-block">{{ form.admission_date.errors.0 }}</div>{% endif %}
                </div>
              </div>
            </div>

            <div class="d-flex gap-2 pt-3">
              <button type="submit" class="btn btn-success">
                <i class="bi bi-check-circle"></i> {% if action == 'Create' %}Add Child{% else %}Update Child{% endif %}
              </button>
              <a href="{% url 'child_list' %}" class="btn btn-outline-secondary">Cancel</a>
            </div>
          </form>
        </div>
      </div>
    </div>

    <div class="col-lg-4">
      <div class="card bg-light">
        <div class="card-body">
          <h6 class="card-title mb-3"><i class="bi bi-info-circle"></i> Need Help?</h6>
          <ul class="small">
            <li><strong>Child ID:</strong> Unique identifier (e.g., CH001)</li>
            <li><strong>Full Name:</strong> Complete name</li>
            <li><strong>Emergency Contact:</strong> Parent/Guardian phone</li>
            <li><strong>Health Status:</strong> Current condition</li>
            <li><strong>Sponsor Status:</strong> Sponsorship availability</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</div>
{% endblock %}
''',

    'children/templates/children/child_list.html': '''{% extends "core/base.html" %}

{% block title %}Children - KafalatCare{% endblock %}

{% block content %}
<div class="container-fluid py-4">
  <div class="d-flex align-items-center justify-content-between mb-4">
    <div>
      <h1 class="h2">Children Management</h1>
      <p class="text-muted">Manage child records and information</p>
    </div>
    <a href="{% url 'child_create' %}" class="btn btn-success">
      <i class="bi bi-plus-circle"></i> Add New Child
    </a>
  </div>

  <!-- Filters -->
  <div class="card shadow-sm mb-4">
    <div class="card-body">
      <form method="get" class="row g-3">
        <div class="col-md-4">
          <input type="text" name="search" class="form-control" placeholder="Search by ID, name, or level..." value="{{ search_query }}">
        </div>
        <div class="col-md-3">
          <select name="sponsor_status" class="form-select">
            <option value="">All Sponsor Status</option>
            <option value="available" {% if sponsor_filter == 'available' %}selected{% endif %}>Available</option>
            <option value="sponsored" {% if sponsor_filter == 'sponsored' %}selected{% endif %}>Sponsored</option>
          </select>
        </div>
        <div class="col-md-3">
          <select name="health_status" class="form-select">
            <option value="">All Health Status</option>
            <option value="healthy" {% if health_filter == 'healthy' %}selected{% endif %}>Healthy</option>
            <option value="under_care" {% if health_filter == 'under_care' %}selected{% endif %}>Under Care</option>
            <option value="medical_care" {% if health_filter == 'medical_care' %}selected{% endif %}>Medical Care</option>
            <option value="observation" {% if health_filter == 'observation' %}selected{% endif %}>Under Observation</option>
          </select>
        </div>
        <div class="col-md-2">
          <button type="submit" class="btn btn-primary w-100">Filter</button>
        </div>
      </form>
    </div>
  </div>

  <!-- Table -->
  <div class="card shadow-sm">
    <div class="table-responsive">
      <table class="table table-hover mb-0">
        <thead class="table-light">
          <tr>
            <th>Child ID</th>
            <th>Full Name</th>
            <th>Age</th>
            <th>Health Status</th>
            <th>Sponsor Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {% for child in children %}
          <tr>
            <td><strong>{{ child.child_id }}</strong></td>
            <td>{{ child.full_name }}</td>
            <td>{{ child.age }}</td>
            <td>
              <span class="badge bg-info">{{ child.get_health_status_display }}</span>
            </td>
            <td>
              <span class="badge {% if child.sponsor_status == 'sponsored' %}bg-success{% else %}bg-warning{% endif %}">
                {{ child.get_sponsor_status_display }}
              </span>
            </td>
            <td>
              <a href="{% url 'child_detail' child.pk %}" class="btn btn-sm btn-outline-primary">
                <i class="bi bi-eye"></i> View
              </a>
              <a href="{% url 'child_update' child.pk %}" class="btn btn-sm btn-outline-warning">
                <i class="bi bi-pencil"></i> Edit
              </a>
              <a href="{% url 'child_delete' child.pk %}" class="btn btn-sm btn-outline-danger">
                <i class="bi bi-trash"></i> Delete
              </a>
            </td>
          </tr>
          {% empty %}
          <tr>
            <td colspan="6" class="text-center py-4 text-muted">No children found</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
</div>
{% endblock %}
''',

    'children/templates/children/child_detail.html': '''{% extends "core/base.html" %}

{% block title %}{{ child.full_name }} - KafalatCare{% endblock %}

{% block content %}
<div class="container-fluid py-4">
  <div class="d-flex align-items-center justify-content-between mb-4">
    <div>
      <h1 class="h2">{{ child.full_name }}</h1>
      <p class="text-muted">Child ID: {{ child.child_id }}</p>
    </div>
    <div class="btn-group" role="group">
      <a href="{% url 'child_update' child.pk %}" class="btn btn-warning">
        <i class="bi bi-pencil"></i> Edit
      </a>
      <a href="{% url 'child_list' %}" class="btn btn-outline-secondary">
        <i class="bi bi-arrow-left"></i> Back
      </a>
    </div>
  </div>

  <div class="row">
    <div class="col-lg-8">
      <!-- Personal Info -->
      <div class="card shadow-sm mb-3">
        <div class="card-header bg-light">
          <h5 class="mb-0">Personal Information</h5>
        </div>
        <div class="card-body">
          <div class="row">
            <div class="col-md-6">
              <p><strong>Full Name:</strong> {{ child.full_name }}</p>
              <p><strong>Date of Birth:</strong> {{ child.date_of_birth|date:"M d, Y" }}</p>
              <p><strong>Age:</strong> {{ child.age }}</p>
            </div>
            <div class="col-md-6">
              <p><strong>Gender:</strong> {{ child.get_gender_display }}</p>
              <p><strong>Admission Date:</strong> {{ child.admission_date|date:"M d, Y" }}</p>
              <p><strong>Emergency Contact:</strong> {{ child.emergency_contact }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Health & Status -->
      <div class="card shadow-sm mb-3">
        <div class="card-header bg-light">
          <h5 class="mb-0">Health & Status</h5>
        </div>
        <div class="card-body">
          <div class="row">
            <div class="col-md-6">
              <p><strong>Health Status:</strong> <span class="badge bg-info">{{ child.get_health_status_display }}</span></p>
              <p><strong>Education Level:</strong> {{ child.education_level }}</p>
            </div>
            <div class="col-md-6">
              <p><strong>Sponsor Status:</strong> <span class="badge bg-success">{{ child.get_sponsor_status_display }}</span></p>
            </div>
          </div>
        </div>
      </div>

      <!-- Health Records -->
      <div class="card shadow-sm mb-3">
        <div class="card-header bg-light d-flex justify-content-between align-items-center">
          <h5 class="mb-0">Latest Health Records</h5>
          <a href="{% url 'health_record_create' %}" class="btn btn-sm btn-success">Add Record</a>
        </div>
        <div class="card-body">
          {% if health_records %}
          <ul class="list-group">
            {% for record in health_records %}
            <li class="list-group-item">
              <strong>{{ record.last_checkup|date:"M d, Y" }}</strong> - Status: {{ record.get_status_display }}
              <a href="#" class="btn btn-sm btn-outline-primary float-end">View</a>
            </li>
            {% endfor %}
          </ul>
          {% else %}
          <p class="text-muted">No health records found</p>
          {% endif %}
        </div>
      </div>

      <!-- Education Records -->
      <div class="card shadow-sm">
        <div class="card-header bg-light d-flex justify-content-between align-items-center">
          <h5 class="mb-0">Latest Education Records</h5>
          <a href="{% url 'education_record_create' %}" class="btn btn-sm btn-success">Add Record</a>
        </div>
        <div class="card-body">
          {% if education_records %}
          <ul class="list-group">
            {% for record in education_records %}
            <li class="list-group-item">
              <strong>{{ record.grade }}</strong> - {{ record.school_name }}
              <a href="#" class="btn btn-sm btn-outline-primary float-end">View</a>
            </li>
            {% endfor %}
          </ul>
          {% else %}
          <p class="text-muted">No education records found</p>
          {% endif %}
        </div>
      </div>
    </div>

    <div class="col-lg-4">
      <div class="card bg-light shadow-sm">
        <div class="card-body">
          <h6 class="card-title mb-3">Quick Info</h6>
          <div class="mb-3">
            <small class="text-muted">Created</small>
            <p class="mb-0">{{ child.created_at|date:"M d, Y g:i A" }}</p>
          </div>
          <div class="mb-3">
            <small class="text-muted">Last Updated</small>
            <p class="mb-0">{{ child.updated_at|date:"M d, Y g:i A" }}</p>
          </div>
          <hr>
          <a href="{% url 'child_delete' child.pk %}" class="btn btn-danger w-100">
            <i class="bi bi-trash"></i> Delete Record
          </a>
        </div>
      </div>
    </div>
  </div>
</div>
{% endblock %}
''',

    'children/templates/children/child_confirm_delete.html': '''{% extends "core/base.html" %}

{% block title %}Delete Child - KafalatCare{% endblock %}

{% block content %}
<div class="container py-5">
  <div class="row justify-content-center">
    <div class="col-md-6">
      <div class="card shadow-lg border-danger">
        <div class="card-body text-center p-5">
          <div class="mb-4">
            <i class="bi bi-exclamation-triangle text-danger" style="font-size: 3rem;"></i>
          </div>
          <h3 class="card-title">Delete Child Record</h3>
          <p class="text-muted mt-3">
            Are you sure you want to delete the record for <strong>{{ child.full_name }}</strong>?
          </p>
          <p class="text-danger small">This action cannot be undone.</p>

          <form method="post" class="mt-4">
            {% csrf_token %}
            <button type="submit" class="btn btn-danger btn-lg">
              <i class="bi bi-trash"></i> Yes, Delete
            </button>
            <a href="{% url 'child_detail' child.pk %}" class="btn btn-outline-secondary btn-lg">Cancel</a>
          </form>
        </div>
      </div>
    </div>
  </div>
</div>
{% endblock %}
''',

    # More templates follow similar patterns...
}


def create_all_templates():
    """Create all template files"""
    base_path = Path(__file__).parent
    
    created_count = 0
    for template_path, content in TEMPLATES.items():
        full_path = base_path / template_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        created_count += 1
        print(f"✓ Created: {template_path}")
    
    print(f"\n✓ Successfully created {created_count} template files!")


if __name__ == '__main__':
    create_all_templates()
