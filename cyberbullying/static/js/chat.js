(function () {
  var root = document.getElementById('chat-root');
  if (!root) return;

  var log = document.getElementById('chat-log');
  var form = document.getElementById('chat-form');
  var input = document.getElementById('chat-input');
  var typingIndicator = document.getElementById('typing-indicator');
  var wsUrl = root.dataset.wsScheme + '://' + root.dataset.wsHost + root.dataset.wsPath;
  var ws = new WebSocket(wsUrl);

  function getCookie(name) {
    var match = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return match ? match.pop() : '';
  }

  function appendMessage(msg, animate) {
    var emptyNotice = log.querySelector('.chat-empty');
    if (emptyNotice) emptyNotice.remove();

    var row = document.createElement('div');
    row.className = 'chat-bubble-row ' + (msg.is_from_admin ? 'from-admin' : 'from-self') + (animate ? ' chat-bubble-enter' : '');
    row.dataset.messageId = msg.id;

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
    meta.textContent = (msg.is_from_admin ? 'Admin' : 'You') + (msg.read_at ? ' - Read' : '');
    bubble.appendChild(meta);

    row.appendChild(bubble);
    log.appendChild(row);
    log.scrollTop = log.scrollHeight;
  }

  function markVisibleMessagesRead() {
    ws.send(JSON.stringify({ type: 'read' }));
  }

  ws.onopen = function () {
    fetch('/api/chat/me/', { credentials: 'same-origin' })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        log.innerHTML = '';
        var messages = data.messages || [];
        if (messages.length === 0) {
          var empty = document.createElement('p');
          empty.className = 'chat-empty';
          empty.textContent = 'No messages yet. Say hello to start the conversation.';
          log.appendChild(empty);
        } else {
          messages.forEach(function (m) { appendMessage(m, false); });
        }
        markVisibleMessagesRead();
      });
  };

  ws.onmessage = function (event) {
    var data = JSON.parse(event.data);
    if (data.type === 'chat.message') {
      appendMessage(data, true);
      if (data.is_from_admin) {
        markVisibleMessagesRead();
      }
    } else if (data.type === 'chat.typing') {
      typingIndicator.textContent = data.is_from_admin ? 'Admin is typing...' : '';
      setTimeout(function () { typingIndicator.textContent = ''; }, 3000);
    } else if (data.type === 'chat.read') {
      var rows = log.querySelectorAll('.chat-bubble-row.from-self');
      rows.forEach(function (row) {
        var meta = row.querySelector('.chat-bubble-meta');
        if (meta && meta.textContent.indexOf('Read') === -1) {
          meta.textContent = 'You - Read';
        }
      });
    }
  };

  var attachmentInput = document.getElementById('chat-attachment');

  function showChatError(message) {
    var notice = document.createElement('p');
    notice.className = 'chat-empty chat-error';
    notice.textContent = message;
    log.appendChild(notice);
    log.scrollTop = log.scrollHeight;
    setTimeout(function () {
      if (notice.parentNode) notice.parentNode.removeChild(notice);
    }, 4000);
  }

  form.addEventListener('submit', function (event) {
    event.preventDefault();
    var body = input.value.trim();
    var file = attachmentInput && attachmentInput.files[0];

    if (!body && !file) {
      showChatError('Type a message or attach a file before sending.');
      return;
    }

    if (file) {
      var formData = new FormData();
      formData.append('file', file);
      fetch('/api/chat/attachments/', {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'X-CSRFToken': getCookie('csrftoken') },
        body: formData,
      }).then(function (res) {
        if (!res.ok) {
          return res.json().catch(function () { return {}; }).then(function (data) {
            showChatError(data.detail || 'The attachment could not be uploaded.');
          });
        }
      }).catch(function () {
        showChatError('The attachment could not be uploaded.');
      });
      attachmentInput.value = '';
    }

    if (body) {
      ws.send(JSON.stringify({ type: 'message', body: body }));
    }
    input.value = '';
  });

  input.addEventListener('input', function () {
    ws.send(JSON.stringify({ type: 'typing' }));
  });
})();
