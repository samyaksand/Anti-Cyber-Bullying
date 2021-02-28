(function () {
  function escapeHtml(value) {
    var div = document.createElement('div');
    div.textContent = value == null ? '' : String(value);
    return div.innerHTML;
  }

  function formatDate(value) {
    if (!value) return '';
    var date = new Date(value);
    if (isNaN(date.getTime())) return value;
    return date.toLocaleString();
  }

  var CATEGORY_LABELS = {
    harassment: 'Harassment',
    cyberbullying: 'Cyberbullying',
    stalking: 'Stalking',
    threats: 'Threats',
    impersonation: 'Impersonation',
    doxxing: 'Doxxing',
    hate_speech: 'Hate speech',
    blackmail: 'Blackmail',
  };

  var categoryChart = null;

  function renderCategoryChart(byCategory) {
    var canvas = document.getElementById('admin-category-chart');
    if (!canvas || typeof Chart === 'undefined') return;
    var labels = byCategory.map(function (row) { return CATEGORY_LABELS[row.category] || row.category; });
    var counts = byCategory.map(function (row) { return row.count; });
    if (categoryChart) {
      categoryChart.data.labels = labels;
      categoryChart.data.datasets[0].data = counts;
      categoryChart.update();
      return;
    }
    categoryChart = new Chart(canvas.getContext('2d'), {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          data: counts,
          backgroundColor: '#e5474b',
          borderRadius: 2,
        }],
      },
      options: {
        legend: { display: false },
        scales: {
          yAxes: [{ ticks: { beginAtZero: true, precision: 0 } }],
        },
      },
    });
  }

  function renderStats(data) {
    var tiles = [
      ['Total complaints', data.total_complaints, ''],
      ['Pending', data.pending_complaints, 'dash-tile-accent'],
      ['Resolved', data.resolved_complaints, ''],
      ['Critical', data.critical_complaints, 'dash-tile-accent'],
      ['Registered users', data.registered_users, ''],
      ['Unread messages', data.unread_messages, data.unread_messages ? 'dash-tile-notify' : ''],
    ];
    var html = tiles.map(function (t) {
      return '<div class="dash-tile ' + t[2] + '">' +
        '<span class="dash-tile-value">' + t[1] + '</span>' +
        '<span class="dash-tile-label">' + t[0] + '</span></div>';
    }).join('');
    document.getElementById('admin-stats').innerHTML = html;
    renderCategoryChart(data.by_category || []);
  }

  function loadStats() {
    return fetch('/api/admin/stats/', { credentials: 'same-origin' })
      .then(function (res) { return res.json(); })
      .then(renderStats);
  }

  loadStats();

  function getCookie(name) {
    var match = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return match ? match.pop() : '';
  }

  function loadInbox() {
    fetch('/api/admin/chat/inbox/', { credentials: 'same-origin' })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        var results = data.results || data;
        var inbox = document.getElementById('admin-inbox');
        if (!results.length) {
          inbox.innerHTML = '<p class="chat-empty">No conversations yet.</p>';
          return;
        }
        var html = '<div class="admin-inbox-list">';
        results.forEach(function (c) {
          var lastBody = c.last_message ? escapeHtml(c.last_message.body || '(attachment)') : 'No messages yet.';
          html += '<div class="admin-inbox-row' + (c.id === activeConversationId ? ' active' : '') + '" data-conversation-id="' + c.id + '">' +
            '<div class="admin-inbox-row-main" onclick="openConversation(' + c.id + '); return false;">' +
            '<div class="admin-inbox-row-head">' +
            '<span class="admin-inbox-user">' + escapeHtml(c.user_display) + '</span>' +
            (c.unread_count ? '<span class="admin-inbox-unread">' + c.unread_count + '</span>' : '') +
            '</div>' +
            '<p class="admin-inbox-preview">' + lastBody + '</p>' +
            '</div>' +
            '<button type="button" class="admin-inbox-toggle" onclick="setConversationStatus(' + c.id + ', \'' +
            (c.status === 'resolved' ? 'open' : 'resolved') + '\')">' +
            (c.status === 'resolved' ? 'Reopen' : 'Resolve') + '</button></div>';
        });
        html += '</div>';
        inbox.innerHTML = html;
      });
  }

  loadInbox();

  window.setConversationStatus = function (conversationId, newStatus) {
    fetch('/api/admin/chat/' + conversationId + '/', {
      method: 'PATCH',
      credentials: 'same-origin',
      headers: { 'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus }),
    }).then(loadInbox);
  };

  var adminWs = null;
  var activeConversationId = null;

  function ensureAdminSocket() {
    if (adminWs && adminWs.readyState === WebSocket.OPEN) return;
    var scheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
    adminWs = new WebSocket(scheme + '://' + window.location.host + '/ws/chat/');
    adminWs.onmessage = function (event) {
      var data = JSON.parse(event.data);
      if (data.type === 'chat.message' && data.conversation_id === activeConversationId) {
        appendAdminChatMessage(data);
      }
    };
  }

  function appendAdminChatMessage(msg) {
    var log = document.getElementById('admin-chat-log');
    var emptyNotice = log.querySelector('.chat-empty');
    if (emptyNotice) emptyNotice.remove();

    var row = document.createElement('div');
    row.className = 'chat-bubble-row ' + (msg.is_from_admin ? 'from-self' : 'from-admin');

    var bubble = document.createElement('div');
    bubble.className = 'chat-bubble';

    var body = document.createElement('p');
    body.className = 'chat-bubble-body';
    body.textContent = msg.body;
    bubble.appendChild(body);

    if (msg.attachment) {
      var link = document.createElement('a');
      link.href = msg.attachment;
      link.className = 'chat-bubble-attachment';
      link.textContent = 'Attachment';
      link.target = '_blank';
      link.rel = 'noopener';
      bubble.appendChild(link);
    }

    var meta = document.createElement('span');
    meta.className = 'chat-bubble-meta';
    meta.textContent = msg.is_from_admin ? 'Admin' : 'User';
    bubble.appendChild(meta);

    row.appendChild(bubble);
    log.appendChild(row);
    log.scrollTop = log.scrollHeight;
  }

  window.openConversation = function (conversationId) {
    activeConversationId = conversationId;
    ensureAdminSocket();
    document.getElementById('admin-chat-panel').style.display = 'block';
    document.querySelectorAll('.admin-inbox-row').forEach(function (row) {
      row.classList.toggle('active', Number(row.dataset.conversationId) === conversationId);
    });
    var log = document.getElementById('admin-chat-log');
    log.innerHTML = '<p class="chat-empty">Loading...</p>';
    fetch('/api/admin/chat/' + conversationId + '/messages/', { credentials: 'same-origin' })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        var results = data.results || data;
        log.innerHTML = '';
        if (!results.length) {
          log.innerHTML = '<p class="chat-empty">No messages yet.</p>';
          return;
        }
        results.forEach(appendAdminChatMessage);
      });
  };

  document.getElementById('admin-chat-form').addEventListener('submit', function (event) {
    event.preventDefault();
    if (!activeConversationId || !adminWs || adminWs.readyState !== WebSocket.OPEN) return;
    var input = document.getElementById('admin-chat-input');
    var body = input.value.trim();
    if (!body) return;
    adminWs.send(JSON.stringify({ type: 'message', body: body, conversation_id: activeConversationId }));
    input.value = '';
  });

  var allComplaints = [];

  function applyComplaintFilters() {
    var search = (document.getElementById('admin-complaint-search').value || '').toLowerCase();
    return allComplaints.filter(function (c) {
      if (!search) return true;
      return c.reference_id.toLowerCase().indexOf(search) !== -1;
    });
  }

  function renderComplaints() {
    var filtered = applyComplaintFilters();
    var container = document.getElementById('admin-complaints');
    if (!filtered.length) {
      container.innerHTML = '<p class="chat-empty">No complaints match the current filters.</p>';
      return;
    }
    var html = '<div class="admin-complaint-list">';
    filtered.forEach(function (c) {
      html += '<div class="admin-complaint-row">' +
        '<div class="admin-complaint-row-head" onclick="toggleComplaintRow(' + c.id + ')">' +
        '<div class="admin-complaint-row-main">' +
        '<span class="dash-case-ref">' + escapeHtml(c.reference_id) + '</span>' +
        '<span class="dash-case-category">' + escapeHtml(c.category_display) + '</span>' +
        '</div>' +
        '<span class="status-badge status-' + c.status + '">' + escapeHtml(c.status_display) + '</span>' +
        '</div>' +
        '<div id="complaint-expanded-' + c.id + '" class="admin-complaint-expanded" style="display:none;">' +
        '<div class="admin-complaint-panels">' +
        '<div id="manage-panel-' + c.id + '" class="admin-manage-panel"></div>' +
        '<div id="evidence-panel-' + c.id + '" class="admin-evidence-panel"></div>' +
        '</div></div></div>';
    });
    html += '</div>';
    container.innerHTML = html;
  }

  window.toggleComplaintRow = function (complaintId) {
    var panel = document.getElementById('complaint-expanded-' + complaintId);
    if (!panel) return;
    var opening = panel.style.display === 'none';
    panel.style.display = opening ? 'block' : 'none';
    if (opening) {
      openComplaintManagement(complaintId);
      loadComplaintEvidence(complaintId);
    }
  };

  function loadComplaints() {
    var statusFilter = document.getElementById('admin-status-filter').value;
    var url = '/api/admin/complaints/' + (statusFilter ? '?status=' + encodeURIComponent(statusFilter) : '');
    fetch(url, { credentials: 'same-origin' })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        allComplaints = data.results || data;
        renderComplaints();
      });
  }

  document.getElementById('admin-complaint-search').addEventListener('input', renderComplaints);
  document.getElementById('admin-status-filter').addEventListener('change', loadComplaints);

  loadComplaints();

  var STATUS_CHOICES = [
    ['submitted', 'Submitted'],
    ['under_review', 'Under Review'],
    ['info_required', 'Additional Information Required'],
    ['in_progress', 'Investigation in Progress'],
    ['resolved', 'Resolved'],
    ['closed', 'Closed'],
  ];

  window.openComplaintManagement = function (complaintId) {
    var panel = document.getElementById('manage-panel-' + complaintId);
    if (!panel) return;
    fetch('/api/admin/complaints/' + complaintId + '/', { credentials: 'same-origin' })
      .then(function (res) { return res.json(); })
      .then(function (complaint) {
        var options = STATUS_CHOICES.map(function (pair) {
          var selected = pair[0] === complaint.status ? ' selected' : '';
          return '<option value="' + pair[0] + '"' + selected + '>' + pair[1] + '</option>';
        }).join('');
        panel.innerHTML =
          '<h3 class="case-subheading">Manage case</h3>' +
          '<div class="field half first"><label>Status</label><select id="status-select-' + complaintId + '">' + options + '</select></div>' +
          '<div class="field"><label>Investigation notes</label><textarea id="notes-' + complaintId + '" rows="3">' +
          escapeHtml(complaint.investigation_notes || '') + '</textarea></div>' +
          '<ul class="actions"><li><button type="button" class="chat-send" onclick="saveComplaintManagement(' + complaintId + ')">Save</button></li></ul>' +
          '<span id="manage-status-' + complaintId + '" class="admin-save-status"></span>';
      });
  };

  window.saveComplaintManagement = function (complaintId) {
    var status = document.getElementById('status-select-' + complaintId).value;
    var notes = document.getElementById('notes-' + complaintId).value;
    fetch('/api/admin/complaints/' + complaintId + '/', {
      method: 'PATCH',
      credentials: 'same-origin',
      headers: { 'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: status, investigation_notes: notes }),
    }).then(function (res) { return res.json(); })
      .then(function () {
        document.getElementById('manage-status-' + complaintId).textContent = 'Saved.';
        loadComplaints();
        loadStats();
      });
  };

  window.loadComplaintEvidence = function (complaintId) {
    var panel = document.getElementById('evidence-panel-' + complaintId);
    if (!panel) {
      return;
    }
    panel.innerHTML = '<h3 class="case-subheading">Evidence</h3><p class="chat-empty">Loading evidence...</p>';
    fetch('/api/complaints/' + complaintId + '/', { credentials: 'same-origin' })
      .then(function (res) { return res.json(); })
      .then(function (complaint) {
        var items = complaint.evidence || [];
        if (!items.length) {
          panel.innerHTML = '<h3 class="case-subheading">Evidence</h3><p class="chat-empty">No evidence uploaded for this complaint.</p>';
          return;
        }
        var html = '<h3 class="case-subheading">Evidence</h3><div class="evidence-items">';
        items.forEach(function (ev) {
          html += '<div class="evidence-item evidence-item-admin">' +
            '<span class="fa fa-file-o evidence-item-icon"></span>' +
            '<div class="evidence-item-body">' +
            '<span class="evidence-item-name">' + escapeHtml(ev.original_filename || ev.file) + '</span>' +
            '<span class="evidence-item-size">' + escapeHtml(ev.file_size) + ' bytes</span>' +
            '<span class="evidence-item-hash">SHA-256: <code>' + escapeHtml(ev.sha256_hash) + '</code></span>' +
            '</div>' +
            '<button type="button" class="case-link evidence-verify-btn" onclick="verifyEvidence(' + ev.id + ')">Verify integrity</button>' +
            '<span id="evidence-status-' + ev.id + '" class="evidence-status"></span>' +
            '<div id="evidence-history-' + ev.id + '" class="evidence-history">' + renderVerifications(ev.verifications) + '</div>' +
            '</div>';
        });
        html += '</div>';
        panel.innerHTML = html;
      });
  };

  function renderVerifications(list) {
    if (!list || !list.length) {
      return '<p class="evidence-no-history">No verification checks have been run yet.</p>';
    }
    var html = '<ul class="evidence-verification-history">';
    list.forEach(function (v) {
      html += '<li>' + escapeHtml(v.result_display) + ' by ' + escapeHtml(v.verified_by_display || 'unknown') +
        ' at ' + escapeHtml(formatDate(v.verified_at)) + '</li>';
    });
    html += '</ul>';
    return html;
  }

  window.verifyEvidence = function (evidenceId) {
    var statusEl = document.getElementById('evidence-status-' + evidenceId);
    var historyEl = document.getElementById('evidence-history-' + evidenceId);
    if (statusEl) {
      statusEl.textContent = 'Checking...';
    }
    fetch('/api/admin/evidence/' + evidenceId + '/verify/', {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'X-CSRFToken': getCookie('csrftoken') },
    })
      .then(function (res) { return res.json(); })
      .then(function (result) {
        if (statusEl) {
          statusEl.textContent = result.result_display;
          statusEl.className = 'evidence-status evidence-status-' + result.result;
        }
        return fetch('/api/admin/evidence/' + evidenceId + '/verifications/', { credentials: 'same-origin' });
      })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        if (historyEl) {
          historyEl.innerHTML = renderVerifications(data.results || data);
        }
      });
  };
})();
