const isAgreed = document.querySelector('#check');
const btn = document.querySelector('#next2');

isAgreed.addEventListener('change', () => {
  if(isAgreed.checked){
    btn.disabled = false;
  } else {
    btn.disabled = true;
  }
    
});