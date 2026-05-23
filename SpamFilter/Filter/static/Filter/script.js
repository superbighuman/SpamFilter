$(document).ready(function () {
    $('#spamForm').submit(function (e) {
        e.preventDefault();
        const form = $(this);
        const submitBtn = form.find('.btn-submit');
        const originalBtnText = submitBtn.html();

        // Show loading state
        submitBtn.prop('disabled', true).html('<i class="fas fa-spinner fa-spin me-2"></i> Analyze...');

        $.ajax({
            type: 'POST',
            url: form.attr('action'),
            data: form.serialize(),
            success: function (response) {
                showResult(response);
            },
            error: function (xhr) {
                alert('Error: ' + xhr.responseJSON.error);
            },
            complete: function () {
                submitBtn.prop('disabled', false).html(originalBtnText);
            }
        });
    });

    function showResult() {
        const resultBox = $('#resultBox');
        const isSpam = data.result === 'SPAM';

        // Reset classes
        resultBox.removeClass('spam not-spam show');

        // Add appropriate classes
        resultBox.addClass(isSpam ? 'spam' : 'not-spam');
        resultBox.addClass('show');

        // Update result text
        $('.result-text').text(isSpam ? 'Это СПАМ' : 'Это не спам');

        // Update confidence meter
        const probability = (data.probability * 100).toFixed(2);
        $('.confidence-value').text(probability + '%');
        $('.progress-bar').css('width', probability + '%');
    }
});
function get_predict() {
    let msgText = document.getElementById("message").value.trim();
    if (!msgText) return alert("Введите текст сообщения");

    fetch("http://localhost:8000/predict/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msgText })
    })
    .then(res => res.json())
    .then(data => {
        console.log("Ответ от /predict/:", data);
        if (data.status === "success") {
            displayResult(data);
        } else if (data.status === "accepted" && data.task_id) {
            console.log("Запускаем опрос для task_id:", data.task_id);
            pollResult(data.task_id);
        } else {
            console.error("Неизвестный статус:", data);
        }
    })
    .catch(err => console.error("Ошибка POST:", err));
}

function pollResult(taskId) {
    let attempts = 0;
    const maxAttempts = 100;
    const interval = setInterval(() => {
        attempts++;
        if (attempts > maxAttempts) {
            clearInterval(interval);
            console.error("Таймаут опроса");
            alert("Сервер долго не отвечает. Попробуйте позже.");
            return;
        }
        fetch(`http://localhost:8000/result/${taskId}/`)
            .then(res => res.json())
            .then(data => {
                console.log(`Опрос #${attempts}:`, data);
                if (data.status === "success") {
                    clearInterval(interval);
                    displayResult(data);
                } else if (data.status === "error") {
                    clearInterval(interval);
                    console.error("Ошибка сервера:", data.error);
                }
                // Если processing, продолжаем
            })
            .catch(err => {
                clearInterval(interval);
                console.error("Ошибка сети при опросе:", err);
            });
    }, 100);
}

function displayResult(answer) {
    const resultBox = $('#resultBox');
    const isSpam = answer.result === 'SPAM';
    resultBox.removeClass('spam not-spam show');
    resultBox.addClass(isSpam ? 'spam' : 'not-spam');
    resultBox.addClass('show');
    $('.result-text').text(isSpam ? 'Это СПАМ' : 'Это не спам');
    const probability = (answer.probability * 100).toFixed(2);
    $('.confidence-value').text(probability + '%');
    $('.progress-bar').css('width', probability + '%');
    console.log("Результат отображён:", answer);
}