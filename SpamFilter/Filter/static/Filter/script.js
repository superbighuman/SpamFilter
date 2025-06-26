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
        $('.result-text').text(isSpam ? 'This letter contains SPAM!' : 'This is ham.');

        // Update confidence meter
        const probability = (data.probability * 100).toFixed(2);
        $('.confidence-value').text(probability + '%');
        $('.progress-bar').css('width', probability + '%');
    }
});

function get_predict() {
    let msg = document.getElementById("message");
    let msgText = msg.value;
    let params = {
        "message": msgText,
    }
    let request = new XMLHttpRequest();
    let url = "http://10.10.5.24:8000/predict/"
    request.open("POST", url, false);
    request.setRequestHeader("Content-Type", "application/json");
    request.send(JSON.stringify(params));
    let answer = JSON.parse(request.responseText);
    console.log(answer.result);

    const resultBox = $('#resultBox');
    const isSpam = answer.result === 'SPAM';

    // Reset classes
    resultBox.removeClass('spam not-spam show');

    // Add appropriate classes
    resultBox.addClass(isSpam ? 'spam' : 'not-spam');
    resultBox.addClass('show');

    // Update result text
    $('.result-text').text(isSpam ? 'This letter contains SPAM!' : 'This is ham.');

    // Update confidence meter
    const probability = (answer.probability * 100).toFixed(2);
    $('.confidence-value').text(probability + '%');
    $('.progress-bar').css('width', probability + '%');
    console.log(request.responseText);


}