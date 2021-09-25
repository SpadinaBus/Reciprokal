/*global SpadinaBus _config*/

var SpadinaBus = window.SpadinaBus || {};

(function getofferWrapper($) {
    var authToken;
    SpadinaBus.authToken.then(function setAuthToken(token) {
        if (token) {
            authToken = token;
        } else {
            window.location.href = '/signin.html';
        }
    }).catch(function handleTokenError(error) {
        alert(error);
        window.location.href = '/signin.html';
    });

    function requestOffer() {
        $.ajax({
            method: 'GET',
            url: _config.api.invokeUrl + '/offer',
            headers: {
                'Authorization': authToken
            },
            contentType: 'application/json',
            success: completeRequest,
            error: function ajaxError(jqXHR, textStatus, errorThrown) {
                console.error('Error requesting data: ', textStatus, ', Details: ', errorThrown);
                console.error('Response: ', jqXHR.responseText);
                alert('An error occured when requesting your offer:\n' + jqXHR.responseText);
            }
        });
    }

    function completeRequest(result) {
        console.log('Response received from API: ', result);
        var offer_id = result.data[0].id
        var json_str = JSON.stringify(result, null, 4);
        
        // Set JSON response
        $('#offer_response_text_area').val(json_str);

        // // SET IMAGE
        // img-name = 
        // img = $(this).find(offer-).text();
        // $('<img />')
        // .attr('src', "" + img + "")         // ADD IMAGE PROPERTIES.
        // .appendTo($('#offer_image'));       // ADD THE IMAGE TO DIV.
    }

    // Register click handler for #request button
    $(function onDocReady() {
        $('#request').click(handleGetofferRequestClick);
        SpadinaBus.authToken.then(function updateAuthMessage(token) {
            if (token) {
                displayUpdate('You are authenticated. Click to see your <a href="#authTokenModal" data-toggle="modal">auth token</a>.');
                $('.authToken').text(token);
            }
        });

        if (!_config.api.invokeUrl) {
            $('#noApiMessage').show();
        }
    });

    function handleGetofferRequestClick(event) {
        requestOffer();
    }

    function displayUpdate(text) {
        $('#updates').append($('<li>' + text + '</li>'));
    }
}(jQuery));
