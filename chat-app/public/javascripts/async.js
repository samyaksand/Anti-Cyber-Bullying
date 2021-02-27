let response;

async function loadMiddleClient() {
  const user_id = this.children[1].id;
  const user_img = this.children[0].src;
  const username = this.children[1].children[0].innerText;

  // update name in middle header
  middleHeader[1].id = user_id;
  middleHeader[0].src = user_img;
  middleHeader[1].innerText = username;
  // console.log(user_id);
  // console.log(user_img);
  // console.log(username);
  
  // add spinner to middle main and fetch msg;
  middleMain.innerHTML = SPINNER;
  
  fetch(`/msg/chat/${user_id}`)
    .then(response => response.json())
    .then((response) => {
      
      let el = '';
      if (response.length == 0) {
        middleMain.innerHTML = INFO('No Messages available');
      } else {
        for (let i = 0; i < response.length; i++) {
          let item = response[i];
          if (item.sender_id == current_user_id) {
            el += `<div class="msg-recived">${item.msg}</div>`;
          } else {
            el += `<div class="msg-sent">${item.msg}</div>`;
          }
        }
        middleMain.innerHTML = `<div>${el}</div>`;
      }
    })
    .catch((err) => {
      middleMain.innerHTML = INFO('Previous data could not be loaded!!!');
    });
}
$(document).on('click', '.users', loadMiddleClient);