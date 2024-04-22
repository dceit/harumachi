document.addEventListener('DOMContentLoaded', event => {
  const urlParams = new URLSearchParams(window.location.search)
  const query = urlParams.get('query')
  const messages = document.querySelectorAll('.card-body > blockquote > p')
  
  messages.forEach(message => {
    const messageText = message.textContent
    const regex = new RegExp(query, 'gi')
    const highlightedText = messageText.replace(regex, `<span style="background-color: #ffb74d; color: black;">$&</span>`)
    
    message.innerHTML = highlightedText
  })
})
