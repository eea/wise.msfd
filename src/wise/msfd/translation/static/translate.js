// Note, this is just orientative, it has no python implementation
//
$(document).ready(function(){

    $("#buton").click(function(e) {
        e.preventDefault();
        var text = $(this).siblings('p').text();
        var target_languages = ['EN'];
        var source_lang = 'ES';
        $.ajax({
            type: "POST",
            url: "/request-translation",
            dataType: 'json',
            data: {
                "text-to-translate": text,
                "targetLanguages": target_languages,
                "sourceLanguage": source_lang,
                "externalReference": text, // set by us, used as identifier
                "sourceObject": window.location.href,
            },
            success: function(result) {
                $.ajax({
                    type: "POST",
                    url: "/request-translation",
                    tryCount : 0,
                    retryLimit : 3,
                    data: {
                        "id": result.transId,
                        "key": result.externalRefId,
                    },
                    success: function(translation) {
                        if (translation) {
                            // debugger;
                            $('.translated').text(translation)
                        }
                        else {
                            this.tryCount++;
                            if (this.tryCount <= this.retryLimit) {
                                //try again
                                $.ajax(this);
                                return;
                            }
                            return;
                        }
                    },
                    error: function (xhr, textStatus, errorThrown) {
                        // debugger;
                        if (textStatus == 'timeout') {
                            this.tryCount++;
                            if (this.tryCount <= this.retryLimit) {
                                //try again
                                $.ajax(this);
                                return;
                            }
                            return;
                        }
                        if (xhr.status == 500) {
                            //handle error
                        } else {
                            //handle error
                        }
                    }});
            },
            error: function(result) {
                debugger;
                alert('error');
            }
        });
    });
});
