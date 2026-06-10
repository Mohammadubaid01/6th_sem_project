let timeLeft = 300;

function startTimer() {
    let timer = setInterval(() => {
        timeLeft--;
        document.getElementById("timer").innerText = timeLeft + "s";

        if (timeLeft <= 0) {
            clearInterval(timer);
            document.getElementById("quizForm").submit();
        }
    }, 1000);
}