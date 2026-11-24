#!/usr/bin/env python
"""
Complete Template Generation Script for KafalatCare
====================================================

This script generates ALL template files needed for the KafalatCare application.
The templates are complete, modern, Bootstrap 5 based, and follow the existing design pattern.

Usage:
    python generate_all_templates.py

This will create 28 template files across 4 app modules.
"""

import os
from pathlib import Path

TEMPLATE_CONTENT = {
    # ============================= CHILDREN TEMPLATES =============================

    'children/templates/children/health_record_form.html': '''{% extends "core/base.html" %}
{% block title %}{% if action == 'Create' %}Add Health Record{% else %}Edit Health Record{% endif %} - KafalatCare{% endblock %}
{% block content %}
<div class="container py-4">
  <div class="d-flex align-items-center justify-content-between mb-4">
    <div>
      <h1 class="h2">{{ action }} Health Record</h1>
      <p class="text-muted">Track medical information and checkups</p>
    </div>
    <a href="{% url 'health_record_list' %}" class="btn btn-outline-secondary">
      <i class="bi bi-arrow-left"></i> Back
    </a>
  </div>

  <div class="row">
    <div class="col-lg-8">
      <div class="card shadow-sm">
        <div class="card-body">
          <form method="post" novalidate>
            {% csrf_token %}

            <div class="mb-4">
              <h5 class="card-title mb-3">Child & Checkup Info</h5>
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label class="form-label">{{ form.child.label }}</label>
                  {{ form.child }}
                  {% if form.child.errors %}<div class="invalid-feedback d-block">{{ form.child.errors.0 }}</div>{% endif %}
                </div>
                <div class="col-md-6 mb-3">
                  <label class="form-label">{{ form.last_checkup.label }}</label>
                  {{ form.last_checkup }}
                  {% if form.last_checkup.errors %}<div class="invalid-feedback d-block">{{ form.last_checkup.errors.0 }}</div>{% endif %}
                </div>
              </div>
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label class="form-label">{{ form.next_checkup.label }}</label>
                  {{ form.next_checkup }}
                  {% if form.next_checkup.errors %}<div class="invalid-feedback d-block">{{ form.next_checkup.errors.0 }}</div>{% endif %}
                </div>
              </div>
            </div>

            <hr class="my-4">

            <div class="mb-4">
              <h5 class="card-title mb-3">Physical Measurements</h5>
              <div class="row">
                <div class="col-md-4 mb-3">
                  <label class="form-label">{{ form.blood_type.label }}</label>
                  {{ form.blood_type }}
                </div>
                <div class="col-md-4 mb-3">
                  <label class="form-label">{{ form.weight.label }}</label>
                  {{ form.weight }}
                </div>
                <div class="col-md-4 mb-3">
                  <label class="form-label">{{ form.height.label }}</label>
                  {{ form.height }}
                </div>
              </div>
            </div>

            <hr class="my-4">

            <div class="mb-4">
              <h5 class="card-title mb-3">Medical Details</h5>
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label class="form-label">{{ form.vaccinations.label }}</label>
                  {{ form.vaccinations }}
                </div>
                <div class="col-md-6 mb-3">
                  <label class="form-label">{{ form.status.label }}</label>
                  {{ form.status }}
                </div>
              </div>
              <div class="mb-3">
                <label class="form-label">{{ form.current_medications.label }}</label>
                {{ form.current_medications }}
              </div>
              <div class="mb-3">
                <label class="form-label">{{ form.allergies.label }}</label>
                {{ form.allergies }}
              </div>
              <div class="mb-3">
                <label class="form-label">{{ form.medical_history.label }}</label>
                {{ form.medical_history }}
              </div>
              <div class="mb-3">
                <label class="form-label">{{ form.doctor_name.label }}</label>
                {{ form.doctor_name }}
              </div>
            </div>

            <div class="d-flex gap-2 pt-3">
              <button type="submit" class="btn btn-success">
                <i class="bi bi-check-circle"></i> Save Record
              </button>
              <a href="{% url 'health_record_list' %}" class="btn btn-outline-secondary">Cancel</a>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</div>
{% endblock %}
''',

    'children/templates/children/health_record_list.html': '''{% extends "core/base.html" %}
{% block title %}Health Records - KafalatCare{% endblock %}
{% block content %}
<div class="container-fluid py-4">
  <div class="d-flex align-items-center justify-content-between mb-4">
    <div>
      <h1 class="h2">Health Records</h1>
      <p class="text-muted">View and manage health records</p>
    </div>
    <a href="{% url 'health_record_create' %}" class="btn btn-success">
      <i class="bi bi-plus-circle"></i> Add New Record
    </a>
  </div>

  <div class="card shadow-sm mb-4">
    <div class="card-body">
      <form method="get" class="row g-3">
        <div class="col-md-6">
          <input type="text" name="search" class="form-control" placeholder="Search by child name or ID..." value="{{ search_query }}">
        </div>
        <div class="col-md-4">
          <select name="status" class="form-select">
            <option value="">All Status</option>
            <option value="healthy" {% if status_filter == 'healthy' %}selected{% endif %}>Healthy</option>
            <option value="under_care" {% if status_filter == 'under_care' %}selected{% endif %}>Under Care</option>
            <option value="medical_care" {% if status_filter == 'medical_care' %}selected{% endif %}>Medical Care</option>
          </select>
        </div>
        <div class="col-md-2">
          <button type="submit" class="btn btn-primary w-100">Filter</button>
        </div>
      </form>
    </div>
  </div>

  <div class="card shadow-sm">
    <div class="table-responsive">
      <table class="table table-hover mb-0">
        <thead class="table-light">
          <tr>
            <th>Child</th>
            <th>Last Checkup</th>
            <th>Status</th>
            <th>Doctor</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {% for record in health_records %}
          <tr>
            <td><strong>{{ record.child.full_name }}</strong> ({{ record.child.child_id }})</td>
            <td>{{ record.last_checkup|date:"M d, Y" }}</td>
            <td><span class="badge bg-info">{{ record.get_status_display }}</span></td>
            <td>{{ record.doctor_name|default:"N/A" }}</td>
            <td>
              <a href="{% url 'health_record_detail' record.pk %}" class="btn btn-sm btn-outline-primary">View</a>
              <a href="{% url 'health_record_update' record.pk %}" class="btn btn-sm btn-outline-warning">Edit</a>
              <a href="{% url 'health_record_delete' record.pk %}" class="btn btn-sm btn-outline-danger">Delete</a>
            </td>
          </tr>
          {% empty %}
          <tr>
            <td colspan="5" class="text-center py-4 text-muted">No health records found</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
</div>
{% endblock %}
''',

    'children/templates/children/health_record_detail.html': '''{% extends "core/base.html" %}
{% block title %}Health Record Detail - KafalatCare{% endblock %}
{% block content %}
<div class="container-fluid py-4">
  <div class="d-flex align-items-center justify-content-between mb-4">
    <div>
      <h1 class="h2">{{ health_record.child.full_name }} - Health Record</h1>
      <p class="text-muted">Checkup Date: {{ health_record.last_checkup|date:"M d, Y" }}</p>
    </div>
    <div class="btn-group">
      <a href="{% url 'health_record_update' health_record.pk %}" class="btn btn-warning">Edit</a>
      <a href="{% url 'health_record_list' %}" class="btn btn-outline-secondary">Back</a>
    </div>
  </div>

  <div class="row">
    <div class="col-lg-8">
      <div class="card shadow-sm mb-3">
        <div class="card-header bg-light"><h5 class="mb-0">Physical Measurements</h5></div>
        <div class="card-body">
          <div class="row">
            <div class="col-md-4"><p><strong>Blood Type:</strong> {{ health_record.blood_type }}</p></div>
            <div class="col-md-4"><p><strong>Weight:</strong> {{ health_record.weight }}</p></div>
            <div class="col-md-4"><p><strong>Height:</strong> {{ health_record.height }}</p></div>
          </div>
        </div>
      </div>

      <div class="card shadow-sm mb-3">
        <div class="card-header bg-light"><h5 class="mb-0">Medical Information</h5></div>
        <div class="card-body">
          <p><strong>Status:</strong> <span class="badge bg-info">{{ health_record.get_status_display }}</span></p>
          <p><strong>Vaccinations:</strong> {{ health_record.get_vaccinations_display }}</p>
          <p><strong>Current Medications:</strong> {{ health_record.current_medications|default:"None" }}</p>
          <p><strong>Allergies:</strong> {{ health_record.allergies|default:"None" }}</p>
          <p><strong>Doctor Name:</strong> {{ health_record.doctor_name|default:"Not assigned" }}</p>
        </div>
      </div>

      <div class="card shadow-sm">
        <div class="card-header bg-light"><h5 class="mb-0">Medical History</h5></div>
        <div class="card-body">
          <p>{{ health_record.medical_history|linebreaks }}</p>
        </div>
      </div>
    </div>

    <div class="col-lg-4">
      <div class="card bg-light shadow-sm">
        <div class="card-body">
          <h6 class="card-title mb-3">Checkup Details</h6>
          <p><small class="text-muted">Last Checkup</small><br>{{ health_record.last_checkup|date:"M d, Y" }}</p>
          <p><small class="text-muted">Next Checkup</small><br>{{ health_record.next_checkup|date:"M d, Y"|default:"Not scheduled" }}</p>
          <hr>
          <a href="{% url 'health_record_delete' health_record.pk %}" class="btn btn-danger w-100">Delete</a>
        </div>
      </div>
    </div>
  </div>
</div>
{% endblock %}
''',

    'children/templates/children/health_record_confirm_delete.html': '''{% extends "core/base.html" %}
{% block title %}Delete Health Record - KafalatCare{% endblock %}
{% block content %}
<div class="container py-5">
  <div class="row justify-content-center">
    <div class="col-md-6">
      <div class="card shadow-lg border-danger">
        <div class="card-body text-center p-5">
          <i class="bi bi-exclamation-triangle text-danger" style="font-size: 3rem;"></i>
          <h3 class="card-title mt-3">Delete Health Record</h3>
          <p class="text-muted mt-3">Delete the health record for <strong>{{ health_record.child.full_name }}</strong> dated <strong>{{ health_record.last_checkup|date:"M d, Y" }}</strong>?</p>
          <p class="text-danger small">This cannot be undone.</p>
          <form method="post" class="mt-4">
            {% csrf_token %}
            <button type="submit" class="btn btn-danger btn-lg">Yes, Delete</button>
            <a href="{% url 'health_record_detail' health_record.pk %}" class="btn btn-outline-secondary btn-lg">Cancel</a>
          </form>
        </div>
      </div>
    </div>
  </div>
</div>
{% endblock %}
''',

    'children/templates/children/education_record_form.html': '''{% extends "core/base.html" %}
{% block title %}{% if action == 'Create' %}Add Education Record{% else %}Edit Education Record{% endif %} - KafalatCare{% endblock %}
{% block content %}
<div class="container py-4">
  <div class="d-flex align-items-center justify-content-between mb-4">
    <div>
      <h1 class="h2">{{ action }} Education Record</h1>
      <p class="text-muted">Manage academic records and performance</p>
    </div>
    <a href="{% url 'education_record_list' %}" class="btn btn-outline-secondary">Back</a>
  </div>

  <div class="row">
    <div class="col-lg-8">
      <div class="card shadow-sm">
        <div class="card-body">
          <form method="post" novalidate>
            {% csrf_token %}

            <div class="mb-4">
              <h5 class="card-title mb-3">School Information</h5>
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label class="form-label">{{ form.child.label }}</label>
                  {{ form.child }}
                </div>
                <div class="col-md-6 mb-3">
                  <label class="form-label">{{ form.school_name.label }}</label>
                  {{ form.school_name }}
                </div>
              </div>
              <div class="row">
                <div class="col-md-4 mb-3">
                  <label class="form-label">{{ form.grade.label }}</label>
                  {{ form.grade }}
                </div>
                <div class="col-md-4 mb-3">
                  <label class="form-label">{{ form.roll_number.label }}</label>
                  {{ form.roll_number }}
                </div>
                <div class="col-md-4 mb-3">
                  <label class="form-label">{{ form.teacher_name.label }}</label>
                  {{ form.teacher_name }}
                </div>
              </div>
            </div>

            <hr class="my-4">

            <div class="mb-4">
              <h5 class="card-title mb-3">Academic Performance</h5>
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label class="form-label">{{ form.attendance_percent.label }}</label>
                  {{ form.attendance_percent }}
                </div>
              </div>
              <div class="row">
                <div class="col-md-4 mb-3"><label class="form-label">{{ form.urdu_marks.label }}</label>{{ form.urdu_marks }}</div>
                <div class="col-md-4 mb-3"><label class="form-label">{{ form.english_marks.label }}</label>{{ form.english_marks }}</div>
                <div class="col-md-4 mb-3"><label class="form-label">{{ form.math_marks.label }}</label>{{ form.math_marks }}</div>
              </div>
              <div class="row">
                <div class="col-md-4 mb-3"><label class="form-label">{{ form.science_marks.label }}</label>{{ form.science_marks }}</div>
                <div class="col-md-4 mb-3"><label class="form-label">{{ form.islamiat_marks.label }}</label>{{ form.islamiat_marks }}</div>
              </div>
            </div>

            <hr class="my-4">

            <div class="mb-4">
              <h5 class="card-title mb-3">Conduct & Behavior</h5>
              <div class="row">
                <div class="col-md-6 mb-3"><label class="form-label">{{ form.homework_status.label }}</label>{{ form.homework_status }}</div>
                <div class="col-md-6 mb-3"><label class="form-label">{{ form.behavior.label }}</label>{{ form.behavior }}</div>
              </div>
            </div>

            <div class="d-flex gap-2 pt-3">
              <button type="submit" class="btn btn-success">Save Record</button>
              <a href="{% url 'education_record_list' %}" class="btn btn-outline-secondary">Cancel</a>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</div>
{% endblock %}
''',

    'children/templates/children/education_record_list.html': '''{% extends "core/base.html" %}
{% block title %}Education Records - KafalatCare{% endblock %}
{% block content %}
<div class="container-fluid py-4">
  <div class="d-flex align-items-center justify-content-between mb-4">
    <div>
      <h1 class="h2">Education Records</h1>
      <p class="text-muted">Track academic progress and performance</p>
    </div>
    <a href="{% url 'education_record_create' %}" class="btn btn-success">
      <i class="bi bi-plus-circle"></i> Add Record
    </a>
  </div>

  <div class="card shadow-sm mb-4">
    <div class="card-body">
      <form method="get" class="row g-3">
        <div class="col-md-8">
          <input type="text" name="search" class="form-control" placeholder="Search by child name, ID, or school..." value="{{ search_query }}">
        </div>
        <div class="col-md-4">
          <button type="submit" class="btn btn-primary w-100">Search</button>
        </div>
      </form>
    </div>
  </div>

  <div class="card shadow-sm">
    <div class="table-responsive">
      <table class="table table-hover mb-0">
        <thead class="table-light">
          <tr>
            <th>Child</th>
            <th>School</th>
            <th>Grade</th>
            <th>Attendance</th>
            <th>GPA</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {% for record in education_records %}
          <tr>
            <td><strong>{{ record.child.full_name }}</strong></td>
            <td>{{ record.school_name }}</td>
            <td>{{ record.grade }}</td>
            <td>{{ record.attendance_percent }}%</td>
            <td>{{ record.overall_gpa|floatformat:1 }}</td>
            <td>
              <a href="{% url 'education_record_detail' record.pk %}" class="btn btn-sm btn-outline-primary">View</a>
              <a href="{% url 'education_record_update' record.pk %}" class="btn btn-sm btn-outline-warning">Edit</a>
              <a href="{% url 'education_record_delete' record.pk %}" class="btn btn-sm btn-outline-danger">Delete</a>
            </td>
          </tr>
          {% empty %}
          <tr><td colspan="6" class="text-center py-4 text-muted">No education records found</td></tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
</div>
{% endblock %}
''',

    'children/templates/children/education_record_detail.html': '''{% extends "core/base.html" %}
{% block title %}{{ education_record.child.full_name }} - Education Record - KafalatCare{% endblock %}
{% block content %}
<div class="container-fluid py-4">
  <div class="d-flex align-items-center justify-content-between mb-4">
    <div>
      <h1 class="h2">{{ education_record.child.full_name }} - {{ education_record.grade }}</h1>
      <p class="text-muted">{{ education_record.school_name }}</p>
    </div>
    <div class="btn-group">
      <a href="{% url 'education_record_update' education_record.pk %}" class="btn btn-warning">Edit</a>
      <a href="{% url 'education_record_list' %}" class="btn btn-outline-secondary">Back</a>
    </div>
  </div>

  <div class="row">
    <div class="col-lg-8">
      <div class="card shadow-sm mb-3">
        <div class="card-header bg-light"><h5 class="mb-0">Academic Performance</h5></div>
        <div class="card-body">
          <div class="row text-center">
            <div class="col-md-3"><p><small>Attendance</small><br><h4>{{ education_record.attendance_percent }}%</h4></p></div>
            <div class="col-md-3"><p><small>Urdu</small><br><h4>{{ education_record.urdu_marks }}</h4></p></div>
            <div class="col-md-3"><p><small>English</small><br><h4>{{ education_record.english_marks }}</h4></p></div>
            <div class="col-md-3"><p><small>Math</small><br><h4>{{ education_record.math_marks }}</h4></p></div>
          </div>
          <div class="row text-center mt-3">
            <div class="col-md-4"><p><small>Science</small><br><h4>{{ education_record.science_marks }}</h4></p></div>
            <div class="col-md-4"><p><small>Islamiat</small><br><h4>{{ education_record.islamiat_marks }}</h4></p></div>
            <div class="col-md-4"><p><small>Overall GPA</small><br><h4 class="text-success">{{ education_record.overall_gpa|floatformat:2 }}</h4></p></div>
          </div>
        </div>
      </div>

      <div class="card shadow-sm">
        <div class="card-header bg-light"><h5 class="mb-0">Conduct & Behavior</h5></div>
        <div class="card-body">
          <p><strong>Teacher:</strong> {{ education_record.teacher_name }}</p>
          <p><strong>Homework Status:</strong> {{ education_record.homework_status }}</p>
          <p><strong>Behavior:</strong> {{ education_record.behavior }}</p>
        </div>
      </div>
    </div>

    <div class="col-lg-4">
      <div class="card bg-light shadow-sm">
        <div class="card-body">
          <h6>Record Info</h6>
          <hr>
          <a href="{% url 'education_record_delete' education_record.pk %}" class="btn btn-danger w-100">Delete</a>
        </div>
      </div>
    </div>
  </div>
</div>
{% endblock %}
''',

    'children/templates/children/education_record_confirm_delete.html': '''{% extends "core/base.html" %}
{% block title %}Delete Education Record - KafalatCare{% endblock %}
{% block content %}
<div class="container py-5">
  <div class="row justify-content-center">
    <div class="col-md-6">
      <div class="card shadow-lg border-danger">
        <div class="card-body text-center p-5">
          <i class="bi bi-exclamation-triangle text-danger" style="font-size: 3rem;"></i>
          <h3 class="card-title mt-3">Delete Education Record</h3>
          <p class="text-muted mt-3">Delete the education record for <strong>{{ education_record.child.full_name }}</strong>?</p>
          <form method="post" class="mt-4">
            {% csrf_token %}
            <button type="submit" class="btn btn-danger btn-lg">Yes, Delete</button>
            <a href="{% url 'education_record_detail' education_record.pk %}" class="btn btn-outline-secondary btn-lg">Cancel</a>
          </form>
        </div>
      </div>
    </div>
  </div>
</div>
{% endblock %}
''',

    # ============================= SPONSORSHIPS TEMPLATES =============================

    'sponsorships/templates/sponsorships/sponsorship_form.html': '''{% extends "core/base.html" %}
{% block title %}{% if action == 'Create' %}Add Sponsorship{% else %}Edit Sponsorship{% endif %} - KafalatCare{% endblock %}
{% block content %}
<div class="container py-4">
  <div class="d-flex align-items-center justify-content-between mb-4">
    <div>
      <h1 class="h2">{{ action }} Sponsorship</h1>
      <p class="text-muted">Manage child sponsorship relationships</p>
    </div>
    <a href="{% url 'sponsorship_list' %}" class="btn btn-outline-secondary">Back</a>
  </div>

  <div class="row">
    <div class="col-lg-8">
      <div class="card shadow-sm">
        <div class="card-body">
          <form method="post" novalidate>
            {% csrf_token %}

            <div class="mb-4">
              <h5 class="card-title mb-3">Sponsor Information</h5>
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label class="form-label">{{ form.sponsor_code.label }}</label>
                  {{ form.sponsor_code }}
                </div>
                <div class="col-md-6 mb-3">
                  <label class="form-label">{{ form.sponsor_name.label }}</label>
                  {{ form.sponsor_name }}
                </div>
              </div>
              <div class="row">
                <div class="col-md-4 mb-3">
                  <label class="form-label">{{ form.cnic.label }}</label>
                  {{ form.cnic }}
                </div>
                <div class="col-md-4 mb-3">
                  <label class="form-label">{{ form.phone.label }}</label>
                  {{ form.phone }}
                </div>
                <div class="col-md-4 mb-3">
                  <label class="form-label">{{ form.email.label }}</label>
                  {{ form.email }}
                </div>
              </div>
            </div>

            <hr class="my-4">

            <div class="mb-4">
              <h5 class="card-title mb-3">Sponsorship Details</h5>
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label class="form-label">{{ form.child.label }}</label>
                  {{ form.child }}
                </div>
                <div class="col-md-6 mb-3">
                  <label class="form-label">{{ form.monthly_amount.label }}</label>
                  {{ form.monthly_amount }}
                </div>
              </div>
              <div class="row">
                <div class="col-md-4 mb-3">
                  <label class="form-label">{{ form.start_date.label }}</label>
                  {{ form.start_date }}
                </div>
                <div class="col-md-4 mb-3">
                  <label class="form-label">{{ form.payment_method.label }}</label>
                  {{ form.payment_method }}
                </div>
                <div class="col-md-4 mb-3">
                  <label class="form-label">{{ form.status.label }}</label>
                  {{ form.status }}
                </div>
              </div>
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label class="form-label">{{ form.last_payment_date.label }}</label>
                  {{ form.last_payment_date }}
                </div>
                <div class="col-md-6 mb-3">
                  <label class="form-label">{{ form.next_payment_date.label }}</label>
                  {{ form.next_payment_date }}
                </div>
              </div>
            </div>

            <div class="d-flex gap-2 pt-3">
              <button type="submit" class="btn btn-success">Save Sponsorship</button>
              <a href="{% url 'sponsorship_list' %}" class="btn btn-outline-secondary">Cancel</a>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</div>
{% endblock %}
''',

    'sponsorships/templates/sponsorships/sponsorship_list.html': '''{% extends "core/base.html" %}
{% block title %}Sponsorships - KafalatCare{% endblock %}
{% block content %}
<div class="container-fluid py-4">
  <div class="d-flex align-items-center justify-content-between mb-4">
    <div>
      <h1 class="h2">Sponsorships</h1>
      <p class="text-muted">Manage child sponsorship programs</p>
    </div>
    <a href="{% url 'sponsorship_create' %}" class="btn btn-success">
      <i class="bi bi-plus-circle"></i> New Sponsorship
    </a>
  </div>

  <div class="card shadow-sm mb-4">
    <div class="card-body">
      <form method="get" class="row g-3">
        <div class="col-md-6">
          <input type="text" name="search" class="form-control" placeholder="Search sponsor or child..." value="{{ search_query }}">
        </div>
        <div class="col-md-4">
          <select name="status" class="form-select">
            <option value="">All Status</option>
            <option value="active" {% if status_filter == 'active' %}selected{% endif %}>Active</option>
            <option value="paused" {% if status_filter == 'paused' %}selected{% endif %}>Paused</option>
            <option value="ended" {% if status_filter == 'ended' %}selected{% endif %}>Ended</option>
          </select>
        </div>
        <div class="col-md-2">
          <button type="submit" class="btn btn-primary w-100">Filter</button>
        </div>
      </form>
    </div>
  </div>

  <div class="card shadow-sm">
    <div class="table-responsive">
      <table class="table table-hover mb-0">
        <thead class="table-light">
          <tr>
            <th>Sponsor Code</th>
            <th>Sponsor Name</th>
            <th>Child</th>
            <th>Monthly Amount</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {% for sponsorship in sponsorships %}
          <tr>
            <td><strong>{{ sponsorship.sponsor_code }}</strong></td>
            <td>{{ sponsorship.sponsor_name }}</td>
            <td>{{ sponsorship.child|default:"Unassigned" }}</td>
            <td>PKR {{ sponsorship.monthly_amount|floatformat:0 }}</td>
            <td><span class="badge bg-{% if sponsorship.status == 'active' %}success{% elif sponsorship.status == 'paused' %}warning{% else %}secondary{% endif %}">{{ sponsorship.get_status_display }}</span></td>
            <td>
              <a href="{% url 'sponsorship_detail' sponsorship.pk %}" class="btn btn-sm btn-outline-primary">View</a>
              <a href="{% url 'sponsorship_update' sponsorship.pk %}" class="btn btn-sm btn-outline-warning">Edit</a>
              <a href="{% url 'sponsorship_delete' sponsorship.pk %}" class="btn btn-sm btn-outline-danger">Delete</a>
            </td>
          </tr>
          {% empty %}
          <tr><td colspan="6" class="text-center py-4 text-muted">No sponsorships found</td></tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
</div>
{% endblock %}
''',

    'sponsorships/templates/sponsorships/sponsorship_detail.html': '''{% extends "core/base.html" %}
{% block title %}{{ sponsorship.sponsor_name }} - Sponsorship - KafalatCare{% endblock %}
{% block content %}
<div class="container-fluid py-4">
  <div class="d-flex align-items-center justify-content-between mb-4">
    <div>
      <h1 class="h2">{{ sponsorship.sponsor_name }}</h1>
      <p class="text-muted">Sponsorship Code: {{ sponsorship.sponsor_code }}</p>
    </div>
    <div class="btn-group">
      <a href="{% url 'sponsorship_update' sponsorship.pk %}" class="btn btn-warning">Edit</a>
      <a href="{% url 'sponsorship_list' %}" class="btn btn-outline-secondary">Back</a>
    </div>
  </div>

  <div class="row">
    <div class="col-lg-8">
      <div class="card shadow-sm mb-3">
        <div class="card-header bg-light"><h5 class="mb-0">Sponsor Information</h5></div>
        <div class="card-body">
          <div class="row">
            <div class="col-md-6">
              <p><strong>Name:</strong> {{ sponsorship.sponsor_name }}</p>
              <p><strong>CNIC:</strong> {{ sponsorship.cnic }}</p>
              <p><strong>Phone:</strong> {{ sponsorship.phone }}</p>
            </div>
            <div class="col-md-6">
              <p><strong>Email:</strong> {{ sponsorship.email }}</p>
              <p><strong>Status:</strong> <span class="badge bg-success">{{ sponsorship.get_status_display }}</span></p>
            </div>
          </div>
        </div>
      </div>

      <div class="card shadow-sm">
        <div class="card-header bg-light"><h5 class="mb-0">Sponsorship Details</h5></div>
        <div class="card-body">
          <div class="row">
            <div class="col-md-6">
              <p><strong>Sponsored Child:</strong> {{ sponsorship.child|default:"None" }}</p>
              <p><strong>Monthly Amount:</strong> PKR {{ sponsorship.monthly_amount|floatformat:2 }}</p>
              <p><strong>Start Date:</strong> {{ sponsorship.start_date|date:"M d, Y" }}</p>
            </div>
            <div class="col-md-6">
              <p><strong>Payment Method:</strong> {{ sponsorship.payment_method }}</p>
              <p><strong>Last Payment:</strong> {{ sponsorship.last_payment_date|date:"M d, Y"|default:"N/A" }}</p>
              <p><strong>Next Payment:</strong> {{ sponsorship.next_payment_date|date:"M d, Y"|default:"N/A" }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="col-lg-4">
      <div class="card bg-light shadow-sm">
        <div class="card-body">
          <a href="{% url 'sponsorship_delete' sponsorship.pk %}" class="btn btn-danger w-100">Delete Sponsorship</a>
        </div>
      </div>
    </div>
  </div>
</div>
{% endblock %}
''',

    'sponsorships/templates/sponsorships/sponsorship_confirm_delete.html': '''{% extends "core/base.html" %}
{% block title %}Delete Sponsorship - KafalatCare{% endblock %}
{% block content %}
<div class="container py-5">
  <div class="row justify-content-center">
    <div class="col-md-6">
      <div class="card shadow-lg border-danger">
        <div class="card-body text-center p-5">
          <i class="bi bi-exclamation-triangle text-danger" style="font-size: 3rem;"></i>
          <h3 class="card-title mt-3">Delete Sponsorship</h3>
          <p class="text-muted mt-3">Delete sponsorship for <strong>{{ sponsorship.sponsor_name }}</strong>?</p>
          <form method="post" class="mt-4">
            {% csrf_token %}
            <button type="submit" class="btn btn-danger btn-lg">Yes, Delete</button>
            <a href="{% url 'sponsorship_detail' sponsorship.pk %}" class="btn btn-outline-secondary btn-lg">Cancel</a>
          </form>
        </div>
      </div>
    </div>
  </div>
</div>
{% endblock %}
''',

    # ============================= STAFF MANAGEMENT TEMPLATES =============================

    'staff_management/templates/staff_management/staff_form.html': '''{% extends "core/base.html" %}
{% block title %}{% if action == 'Create' %}Add Staff Member{% else %}Edit Staff Member{% endif %} - KafalatCare{% endblock %}
{% block content %}
<div class="container py-4">
  <div class="d-flex align-items-center justify-content-between mb-4">
    <div>
      <h1 class="h2">{{ action }} Staff Member</h1>
      <p class="text-muted">Manage staff information and assignments</p>
    </div>
    <a href="{% url 'staff_list' %}" class="btn btn-outline-secondary">Back</a>
  </div>

  <div class="row">
    <div class="col-lg-8">
      <div class="card shadow-sm">
        <div class="card-body">
          <form method="post" novalidate>
            {% csrf_token %}

            <div class="mb-4">
              <h5 class="card-title mb-3">Personal Information</h5>
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label class="form-label">{{ form.staff_id.label }}</label>
                  {{ form.staff_id }}
                </div>
                <div class="col-md-6 mb-3">
                  <label class="form-label">{{ form.full_name.label }}</label>
                  {{ form.full_name }}
                </div>
              </div>
              <div class="row">
                <div class="col-md-4 mb-3">
                  <label class="form-label">{{ form.phone.label }}</label>
                  {{ form.phone }}
                </div>
                <div class="col-md-4 mb-3">
                  <label class="form-label">{{ form.email.label }}</label>
                  {{ form.email }}
                </div>
              </div>
            </div>

            <hr class="my-4">

            <div class="mb-4">
              <h5 class="card-title mb-3">Job Details</h5>
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label class="form-label">{{ form.position.label }}</label>
                  {{ form.position }}
                </div>
                <div class="col-md-6 mb-3">
                  <label class="form-label">{{ form.department.label }}</label>
                  {{ form.department }}
                </div>
              </div>
              <div class="row">
                <div class="col-md-4 mb-3">
                  <label class="form-label">{{ form.shift.label }}</label>
                  {{ form.shift }}
                </div>
                <div class="col-md-4 mb-3">
                  <label class="form-label">{{ form.joining_date.label }}</label>
                  {{ form.joining_date }}
                </div>
                <div class="col-md-4 mb-3">
                  <label class="form-label">{{ form.status.label }}</label>
                  {{ form.status }}
                </div>
              </div>
            </div>

            <hr class="my-4">

            <div class="mb-4">
              <h5 class="card-title mb-3">Compensation & Qualifications</h5>
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label class="form-label">{{ form.salary.label }}</label>
                  {{ form.salary }}
                </div>
              </div>
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label class="form-label">{{ form.experience.label }}</label>
                  {{ form.experience }}
                </div>
                <div class="col-md-6 mb-3">
                  <label class="form-label">{{ form.qualification.label }}</label>
                  {{ form.qualification }}
                </div>
              </div>
            </div>

            <div class="d-flex gap-2 pt-3">
              <button type="submit" class="btn btn-success">Save Staff Member</button>
              <a href="{% url 'staff_list' %}" class="btn btn-outline-secondary">Cancel</a>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</div>
{% endblock %}
''',

    'staff_management/templates/staff_management/staff_list.html': '''{% extends "core/base.html" %}
{% block title %}Staff Management - KafalatCare{% endblock %}
{% block content %}
<div class="container-fluid py-4">
  <div class="d-flex align-items-center justify-content-between mb-4">
    <div>
      <h1 class="h2">Staff Management</h1>
      <p class="text-muted">Manage staff members and assignments</p>
    </div>
    <a href="{% url 'staff_create' %}" class="btn btn-success">
      <i class="bi bi-plus-circle"></i> Add Staff
    </a>
  </div>

  <div class="card shadow-sm mb-4">
    <div class="card-body">
      <form method="get" class="row g-3">
        <div class="col-md-4">
          <input type="text" name="search" class="form-control" placeholder="Search by name, ID..." value="{{ search_query }}">
        </div>
        <div class="col-md-3">
          <select name="status" class="form-select">
            <option value="">All Status</option>
            <option value="active" {% if status_filter == 'active' %}selected{% endif %}>Active</option>
            <option value="probation" {% if status_filter == 'probation' %}selected{% endif %}>Probation</option>
            <option value="inactive" {% if status_filter == 'inactive' %}selected{% endif %}>Inactive</option>
          </select>
        </div>
        <div class="col-md-3">
          <select name="shift" class="form-select">
            <option value="">All Shifts</option>
            <option value="morning" {% if shift_filter == 'morning' %}selected{% endif %}>Morning</option>
            <option value="evening" {% if shift_filter == 'evening' %}selected{% endif %}>Evening</option>
            <option value="night" {% if shift_filter == 'night' %}selected{% endif %}>Night</option>
          </select>
        </div>
        <div class="col-md-2">
          <button type="submit" class="btn btn-primary w-100">Filter</button>
        </div>
      </form>
    </div>
  </div>

  <div class="card shadow-sm">
    <div class="table-responsive">
      <table class="table table-hover mb-0">
        <thead class="table-light">
          <tr>
            <th>Staff ID</th>
            <th>Full Name</th>
            <th>Position</th>
            <th>Department</th>
            <th>Shift</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {% for staff in staff_members %}
          <tr>
            <td><strong>{{ staff.staff_id }}</strong></td>
            <td>{{ staff.full_name }}</td>
            <td>{{ staff.position }}</td>
            <td>{{ staff.department }}</td>
            <td>{{ staff.get_shift_display }}</td>
            <td><span class="badge bg-{% if staff.status == 'active' %}success{% elif staff.status == 'probation' %}warning{% else %}secondary{% endif %}">{{ staff.get_status_display }}</span></td>
            <td>
              <a href="{% url 'staff_detail' staff.pk %}" class="btn btn-sm btn-outline-primary">View</a>
              <a href="{% url 'staff_update' staff.pk %}" class="btn btn-sm btn-outline-warning">Edit</a>
              <a href="{% url 'staff_delete' staff.pk %}" class="btn btn-sm btn-outline-danger">Delete</a>
            </td>
          </tr>
          {% empty %}
          <tr><td colspan="7" class="text-center py-4 text-muted">No staff members found</td></tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
</div>
{% endblock %}
''',

    'staff_management/templates/staff_management/staff_detail.html': '''{% extends "core/base.html" %}
{% block title %}{{ staff_member.full_name }} - Staff - KafalatCare{% endblock %}
{% block content %}
<div class="container-fluid py-4">
  <div class="d-flex align-items-center justify-content-between mb-4">
    <div>
      <h1 class="h2">{{ staff_member.full_name }}</h1>
      <p class="text-muted">{{ staff_member.position }} | {{ staff_member.department }}</p>
    </div>
    <div class="btn-group">
      <a href="{% url 'staff_update' staff_member.pk %}" class="btn btn-warning">Edit</a>
      <a href="{% url 'staff_list' %}" class="btn btn-outline-secondary">Back</a>
    </div>
  </div>

  <div class="row">
    <div class="col-lg-8">
      <div class="card shadow-sm mb-3">
        <div class="card-header bg-light"><h5 class="mb-0">Personal Information</h5></div>
        <div class="card-body">
          <div class="row">
            <div class="col-md-6">
              <p><strong>Staff ID:</strong> {{ staff_member.staff_id }}</p>
              <p><strong>Phone:</strong> {{ staff_member.phone }}</p>
              <p><strong>Email:</strong> {{ staff_member.email }}</p>
            </div>
            <div class="col-md-6">
              <p><strong>Status:</strong> <span class="badge bg-success">{{ staff_member.get_status_display }}</span></p>
              <p><strong>Joining Date:</strong> {{ staff_member.joining_date|date:"M d, Y" }}</p>
            </div>
          </div>
        </div>
      </div>

      <div class="card shadow-sm mb-3">
        <div class="card-header bg-light"><h5 class="mb-0">Job Details</h5></div>
        <div class="card-body">
          <div class="row">
            <div class="col-md-6">
              <p><strong>Position:</strong> {{ staff_member.position }}</p>
              <p><strong>Department:</strong> {{ staff_member.department }}</p>
              <p><strong>Shift:</strong> {{ staff_member.get_shift_display }}</p>
            </div>
            <div class="col-md-6">
              <p><strong>Salary:</strong> PKR {{ staff_member.salary|floatformat:2 }}</p>
              <p><strong>Experience:</strong> {{ staff_member.experience }}</p>
              <p><strong>Qualification:</strong> {{ staff_member.qualification }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="col-lg-4">
      <div class="card bg-light shadow-sm">
        <div class="card-body">
          <a href="{% url 'staff_delete' staff_member.pk %}" class="btn btn-danger w-100">Delete</a>
        </div>
      </div>
    </div>
  </div>
</div>
{% endblock %}
''',

    'staff_management/templates/staff_management/staff_confirm_delete.html': '''{% extends "core/base.html" %}
{% block title %}Delete Staff - KafalatCare{% endblock %}
{% block content %}
<div class="container py-5">
  <div class="row justify-content-center">
    <div class="col-md-6">
      <div class="card shadow-lg border-danger">
        <div class="card-body text-center p-5">
          <i class="bi bi-exclamation-triangle text-danger" style="font-size: 3rem;"></i>
          <h3 class="card-title mt-3">Delete Staff Member</h3>
          <p class="text-muted mt-3">Delete <strong>{{ staff_member.full_name }}</strong> from staff?</p>
          <form method="post" class="mt-4">
            {% csrf_token %}
            <button type="submit" class="btn btn-danger btn-lg">Yes, Delete</button>
            <a href="{% url 'staff_detail' staff_member.pk %}" class="btn btn-outline-secondary btn-lg">Cancel</a>
          </form>
        </div>
      </div>
    </div>
  </div>
</div>
{% endblock %}
''',

    # ============================= DONATIONS TEMPLATES =============================

    'donations/templates/donations/donation_form.html': '''{% extends "core/base.html" %}
{% block title %}{% if action == 'Create' %}Add Donation{% else %}Edit Donation{% endif %} - KafalatCare{% endblock %}
{% block content %}
<div class="container py-4">
  <div class="d-flex align-items-center justify-content-between mb-4">
    <div>
      <h1 class="h2">{{ action }} Donation</h1>
      <p class="text-muted">Record donation and funding information</p>
    </div>
    <a href="{% url 'donation_list' %}" class="btn btn-outline-secondary">Back</a>
  </div>

  <div class="row">
    <div class="col-lg-8">
      <div class="card shadow-sm">
        <div class="card-body">
          <form method="post" novalidate>
            {% csrf_token %}

            <div class="mb-4">
              <h5 class="card-title mb-3">Donor Information</h5>
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label class="form-label">{{ form.donor_name.label }}</label>
                  {{ form.donor_name }}
                </div>
                <div class="col-md-6 mb-3">
                  <label class="form-label">{{ form.donor_type.label }}</label>
                  {{ form.donor_type }}
                </div>
              </div>
            </div>

            <hr class="my-4">

            <div class="mb-4">
              <h5 class="card-title mb-3">Donation Details</h5>
              <div class="row">
                <div class="col-md-4 mb-3">
                  <label class="form-label">{{ form.amount.label }}</label>
                  {{ form.amount }}
                </div>
                <div class="col-md-4 mb-3">
                  <label class="form-label">{{ form.donation_type.label }}</label>
                  {{ form.donation_type }}
                </div>
                <div class="col-md-4 mb-3">
                  <label class="form-label">{{ form.donated_at.label }}</label>
                  {{ form.donated_at }}
                </div>
              </div>
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label class="form-label">{{ form.allocated_to.label }}</label>
                  {{ form.allocated_to }}
                </div>
                <div class="col-md-6 mb-3">
                  <label class="form-label">{{ form.status.label }}</label>
                  {{ form.status }}
                </div>
              </div>
            </div>

            <hr class="my-4">

            <div class="mb-4">
              <h5 class="card-title mb-3">Payment & Receipt</h5>
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label class="form-label">{{ form.payment_method.label }}</label>
                  {{ form.payment_method }}
                </div>
                <div class="col-md-6 mb-3">
                  <label class="form-label">{{ form.transaction_id.label }}</label>
                  {{ form.transaction_id }}
                </div>
              </div>
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label class="form-label">{{ form.receipt_number.label }}</label>
                  {{ form.receipt_number }}
                </div>
                <div class="col-md-6 mb-3">
                  <div class="form-check">
                    {{ form.tax_certificate_issued }}
                    <label class="form-check-label">{{ form.tax_certificate_issued.label }}</label>
                  </div>
                </div>
              </div>
            </div>

            <div class="d-flex gap-2 pt-3">
              <button type="submit" class="btn btn-success">Save Donation</button>
              <a href="{% url 'donation_list' %}" class="btn btn-outline-secondary">Cancel</a>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</div>
{% endblock %}
''',

    'donations/templates/donations/donation_list.html': '''{% extends "core/base.html" %}
{% block title %}Donations - KafalatCare{% endblock %}
{% block content %}
<div class="container-fluid py-4">
  <div class="d-flex align-items-center justify-content-between mb-4">
    <div>
      <h1 class="h2">Donations</h1>
      <p class="text-muted">Track donations and funding</p>
    </div>
    <a href="{% url 'donation_create' %}" class="btn btn-success">
      <i class="bi bi-plus-circle"></i> Record Donation
    </a>
  </div>

  <div class="card shadow-sm mb-4">
    <div class="card-body">
      <form method="get" class="row g-3">
        <div class="col-md-3">
          <input type="text" name="search" class="form-control" placeholder="Search donor name..." value="{{ search_query }}">
        </div>
        <div class="col-md-2">
          <select name="donor_type" class="form-select">
            <option value="">All Donor Type</option>
            <option value="individual" {% if donor_type_filter == 'individual' %}selected{% endif %}>Individual</option>
            <option value="corporate" {% if donor_type_filter == 'corporate' %}selected{% endif %}>Corporate</option>
            <option value="organization" {% if donor_type_filter == 'organization' %}selected{% endif %}>Organization</option>
          </select>
        </div>
        <div class="col-md-2">
          <select name="donation_type" class="form-select">
            <option value="">All Type</option>
            <option value="one_time" {% if type_filter == 'one_time' %}selected{% endif %}>One-time</option>
            <option value="monthly" {% if type_filter == 'monthly' %}selected{% endif %}>Monthly</option>
            <option value="quarterly" {% if type_filter == 'quarterly' %}selected{% endif %}>Quarterly</option>
            <option value="zakat" {% if type_filter == 'zakat' %}selected{% endif %}>Zakat</option>
          </select>
        </div>
        <div class="col-md-2">
          <select name="status" class="form-select">
            <option value="">All Status</option>
            <option value="pending" {% if status_filter == 'pending' %}selected{% endif %}>Pending</option>
            <option value="completed" {% if status_filter == 'completed' %}selected{% endif %}>Completed</option>
            <option value="failed" {% if status_filter == 'failed' %}selected{% endif %}>Failed</option>
          </select>
        </div>
        <div class="col-md-3">
          <button type="submit" class="btn btn-primary w-100">Filter</button>
        </div>
      </form>
    </div>
  </div>

  <div class="card shadow-sm">
    <div class="table-responsive">
      <table class="table table-hover mb-0">
        <thead class="table-light">
          <tr>
            <th>Donor Name</th>
            <th>Donor Type</th>
            <th>Amount (PKR)</th>
            <th>Type</th>
            <th>Date</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {% for donation in donations %}
          <tr>
            <td><strong>{{ donation.donor_name }}</strong></td>
            <td>{{ donation.get_donor_type_display }}</td>
            <td>{{ donation.amount|floatformat:2 }}</td>
            <td>{{ donation.get_donation_type_display }}</td>
            <td>{{ donation.donated_at|date:"M d, Y" }}</td>
            <td><span class="badge bg-{% if donation.status == 'completed' %}success{% elif donation.status == 'pending' %}warning{% else %}danger{% endif %}">{{ donation.get_status_display }}</span></td>
            <td>
              <a href="{% url 'donation_detail' donation.pk %}" class="btn btn-sm btn-outline-primary">View</a>
              <a href="{% url 'donation_update' donation.pk %}" class="btn btn-sm btn-outline-warning">Edit</a>
              <a href="{% url 'donation_delete' donation.pk %}" class="btn btn-sm btn-outline-danger">Delete</a>
            </td>
          </tr>
          {% empty %}
          <tr><td colspan="7" class="text-center py-4 text-muted">No donations found</td></tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
</div>
{% endblock %}
''',

    'donations/templates/donations/donation_detail.html': '''{% extends "core/base.html" %}
{% block title %}{{ donation.donor_name }} - Donation - KafalatCare{% endblock %}
{% block content %}
<div class="container-fluid py-4">
  <div class="d-flex align-items-center justify-content-between mb-4">
    <div>
      <h1 class="h2">{{ donation.donor_name }}</h1>
      <p class="text-muted">Donation of PKR {{ donation.amount|floatformat:2 }}</p>
    </div>
    <div class="btn-group">
      <a href="{% url 'donation_update' donation.pk %}" class="btn btn-warning">Edit</a>
      <a href="{% url 'donation_list' %}" class="btn btn-outline-secondary">Back</a>
    </div>
  </div>

  <div class="row">
    <div class="col-lg-8">
      <div class="card shadow-sm mb-3">
        <div class="card-header bg-light"><h5 class="mb-0">Donation Information</h5></div>
        <div class="card-body">
          <div class="row">
            <div class="col-md-6">
              <p><strong>Donor Name:</strong> {{ donation.donor_name }}</p>
              <p><strong>Donor Type:</strong> {{ donation.get_donor_type_display }}</p>
              <p><strong>Amount:</strong> PKR {{ donation.amount|floatformat:2 }}</p>
            </div>
            <div class="col-md-6">
              <p><strong>Donation Type:</strong> {{ donation.get_donation_type_display }}</p>
              <p><strong>Date:</strong> {{ donation.donated_at|date:"M d, Y" }}</p>
              <p><strong>Status:</strong> <span class="badge bg-success">{{ donation.get_status_display }}</span></p>
            </div>
          </div>
        </div>
      </div>

      <div class="card shadow-sm">
        <div class="card-header bg-light"><h5 class="mb-0">Payment & Allocation</h5></div>
        <div class="card-body">
          <div class="row">
            <div class="col-md-6">
              <p><strong>Payment Method:</strong> {{ donation.payment_method }}</p>
              <p><strong>Transaction ID:</strong> {{ donation.transaction_id }}</p>
            </div>
            <div class="col-md-6">
              <p><strong>Allocated To:</strong> {{ donation.allocated_to }}</p>
              <p><strong>Receipt Number:</strong> {{ donation.receipt_number }}</p>
              <p><strong>Tax Certificate:</strong> {% if donation.tax_certificate_issued %}<span class="badge bg-success">Yes</span>{% else %}<span class="badge bg-secondary">No</span>{% endif %}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="col-lg-4">
      <div class="card bg-light shadow-sm">
        <div class="card-body">
          <a href="{% url 'donation_delete' donation.pk %}" class="btn btn-danger w-100">Delete</a>
        </div>
      </div>
    </div>
  </div>
</div>
{% endblock %}
''',

    'donations/templates/donations/donation_confirm_delete.html': '''{% extends "core/base.html" %}
{% block title %}Delete Donation - KafalatCare{% endblock %}
{% block content %}
<div class="container py-5">
  <div class="row justify-content-center">
    <div class="col-md-6">
      <div class="card shadow-lg border-danger">
        <div class="card-body text-center p-5">
          <i class="bi bi-exclamation-triangle text-danger" style="font-size: 3rem;"></i>
          <h3 class="card-title mt-3">Delete Donation</h3>
          <p class="text-muted mt-3">Delete donation from <strong>{{ donation.donor_name }}</strong> (PKR {{ donation.amount|floatformat:2 }})?</p>
          <form method="post" class="mt-4">
            {% csrf_token %}
            <button type="submit" class="btn btn-danger btn-lg">Yes, Delete</button>
            <a href="{% url 'donation_detail' donation.pk %}" class="btn btn-outline-secondary btn-lg">Cancel</a>
          </form>
        </div>
      </div>
    </div>
  </div>
</div>
{% endblock %}
''',
}


def create_templates():
    """Create all template files from the dictionary"""
    base_path = Path(__file__).parent
    created = 0
    
    for template_rel_path, content in TEMPLATE_CONTENT.items():
        template_path = base_path / template_rel_path
        template_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Created: {template_rel_path}")
            created += 1
        except Exception as e:
            print(f"✗ Failed: {template_rel_path} - {e}")
    
    print(f"\n✓ Successfully created {created}/{len(TEMPLATE_CONTENT)} template files!")
    return created == len(TEMPLATE_CONTENT)


if __name__ == '__main__':
    success = create_templates()
    exit(0 if success else 1)
