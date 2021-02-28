(function () {
  var root = document.getElementById('complaint-detail-root');
  if (!root) return;

  var complaintId = root.dataset.complaintId;
  var trackingCode = root.dataset.trackingCode || '';

  function getCookie(name) {
    var match = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return match ? match.pop() : '';
  }

  function withTrackingCode(url) {
    if (!trackingCode) return url;
    var sep = url.indexOf('?') === -1 ? '?' : '&';
    return url + sep + 'tracking_code=' + encodeURIComponent(trackingCode);
  }

  function csrfHeaders() {
    return { 'X-CSRFToken': getCookie('csrftoken') };
  }

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

  function formatBytes(bytes) {
    if (!bytes && bytes !== 0) return '';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  }

  function loadIncidents() {
    fetch(withTrackingCode('/api/complaints/' + complaintId + '/incidents/'), { credentials: 'same-origin' })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        var items = data.results || data;
        var list = document.getElementById('incident-list');
        if (!items.length) {
          list.innerHTML = '<p class="chat-empty">No incidents recorded yet.</p>';
          return;
        }
        var html = '<div class="incident-items">';
        items.forEach(function (i) {
          html += '<div class="incident-item">' +
            '<div class="incident-item-head">' +
            '<span class="incident-item-date">' + escapeHtml(formatDate(i.occurred_at)) + '</span>' +
            (i.platform ? '<span class="incident-item-platform">' + escapeHtml(i.platform) + '</span>' : '') +
            '</div>' +
            '<p class="incident-item-description">' + escapeHtml(i.description) + '</p>' +
            (i.url ? '<a href="' + escapeHtml(i.url) + '" target="_blank" rel="noopener" class="case-link">View link</a>' : '') +
            '</div>';
        });
        html += '</div>';
        list.innerHTML = html;
      });
  }

  function loadEvidence() {
    fetch(withTrackingCode('/api/complaints/' + complaintId + '/'), { credentials: 'same-origin' })
      .then(function (res) { return res.json(); })
      .then(function (complaint) {
        var items = complaint.evidence || [];
        var list = document.getElementById('evidence-list');
        if (!items.length) {
          list.innerHTML = '<p class="chat-empty">No evidence uploaded yet.</p>';
          return;
        }
        var html = '<div class="evidence-items">';
        items.forEach(function (ev) {
          html += '<div class="evidence-item">' +
            '<span class="fa fa-file-o evidence-item-icon"></span>' +
            '<div class="evidence-item-body">' +
            '<span class="evidence-item-name">' + escapeHtml(ev.original_filename || ev.file) + '</span>' +
            '<span class="evidence-item-size">' + escapeHtml(formatBytes(ev.file_size)) + '</span>' +
            '</div></div>';
        });
        html += '</div>';
        list.innerHTML = html;
      });
  }

  document.getElementById('incident-form').addEventListener('submit', function (event) {
    event.preventDefault();
    var occurredAt = document.getElementById('incident-occurred-at').value;
    var platform = document.getElementById('incident-platform').value;
    var description = document.getElementById('incident-description').value;
    var url = document.getElementById('incident-url').value;

    var formData = new FormData();
    formData.append('occurred_at', occurredAt);
    formData.append('platform', platform);
    formData.append('description', description);
    formData.append('url', url);

    fetch(withTrackingCode('/api/complaints/' + complaintId + '/incidents/'), {
      method: 'POST',
      credentials: 'same-origin',
      headers: csrfHeaders(),
      body: formData,
    }).then(function (res) {
      if (res.ok) {
        event.target.reset();
        loadIncidents();
      }
    });
  });

  document.getElementById('evidence-form').addEventListener('submit', function (event) {
    event.preventDefault();
    var fileInput = document.getElementById('evidence-file');
    if (!fileInput.files[0]) return;

    var formData = new FormData();
    formData.append('file', fileInput.files[0]);

    fetch(withTrackingCode('/api/complaints/' + complaintId + '/evidence/'), {
      method: 'POST',
      credentials: 'same-origin',
      headers: csrfHeaders(),
      body: formData,
    }).then(function (res) {
      if (res.ok) {
        event.target.reset();
        loadEvidence();
      }
    });
  });

  document.getElementById('message-form').addEventListener('submit', function (event) {
    event.preventDefault();
    var input = document.getElementById('message-input');
    var body = input.value.trim();
    if (!body) return;

    var formData = new FormData();
    formData.append('body', body);

    fetch(withTrackingCode('/api/complaints/' + complaintId + '/messages/'), {
      method: 'POST',
      credentials: 'same-origin',
      headers: csrfHeaders(),
      body: formData,
    }).then(function (res) { return res.json(); })
      .then(function (msg) {
        var list = document.getElementById('message-list');
        var emptyNotice = list.querySelector('.chat-empty');
        if (emptyNotice) emptyNotice.remove();

        var row = document.createElement('div');
        row.className = 'chat-bubble-row ' + (msg.author_is_admin ? 'from-admin' : 'from-self');

        var bubble = document.createElement('div');
        bubble.className = 'chat-bubble';

        var bodyEl = document.createElement('p');
        bodyEl.className = 'chat-bubble-body';
        bodyEl.textContent = msg.body;
        bubble.appendChild(bodyEl);

        var meta = document.createElement('span');
        meta.className = 'chat-bubble-meta';
        meta.textContent = msg.author_is_admin ? 'Admin' : (msg.author_name || 'You');
        bubble.appendChild(meta);

        row.appendChild(bubble);
        list.appendChild(row);
        list.scrollTop = list.scrollHeight;
        input.value = '';
      });
  });

  loadIncidents();
  loadEvidence();
})();
