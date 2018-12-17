$(document).ready(function(){

	var auto_translation = function(e) {
			e.preventDefault();
			// debugger;
			var text_div = $(this).parent().parent('ul').parent('div').siblings('div');
			var text = text_div.children('.text').text();
			var buton = $(this);
			var target_languages = ['EN'];
			var source_lang = 'EN';
			//debugger;
			$.ajax({
					text_div: text_div,
					type: "POST",
					url: "./request-translation2",
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
									url: "./request-translation2",
									tryCount : 0,
									retryLimit : 20,
									data: {
											"from_annot": result.externalRefId,
									},
									success: function(translation) {
											if (translation) {
													//debugger;
													//text_div.children('.transl').text(translation)
													location.reload();
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
											//debugger;
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
							//debugger;
							alert('error');
					}
			});
	};

	var edit_translation = function(e) {
		//e.preventDefault();

		var text_div = $(this).parent().parent('ul').parent('div').siblings('div');
		var old_translation = text_div.children('.transl').text();
		var orig_text = text_div.children('.text').text();

		$('#transl-original-text').text(orig_text);
		$('#transl-old-translation').text(old_translation);
		$('#form-edit-translation')[0].elements['new_transl'].value = old_translation

	};

	var submit_translation = function(e) {
		e.preventDefault();

		var orig_text = $(this).parent().parent().siblings('#transl-original-text').text()

		var form = $(this).parent().parent();
		var translation = form[0].elements['new_transl'].value

		//debugger;

		$.ajax({
				form: form,
				type: 'POST',
				url: './translation-callback2',
				dataType: 'json',
				data: {
					'external-reference': orig_text,
					'translation': translation
				},
				success: function(result) {
					//debugger;
					location.reload();
				},
				error: function(result) {
					alert('ERROR saving translation!');
				}
		});
	};

	var show_original = function(e) {
		//debugger;
		$(this)[0].classList.add('active')
		$(this).siblings('.btn-translate-transl')[0].classList.remove('active')

		$(this).parents('td.translatable')[0].classList.remove('blue')
		$(this).parents('td.translatable')[0].classList.remove('green')
		$(this).parents('td.translatable')[0].classList.add('blue')

		$(this).parent().siblings('.text')[0].classList.add('active')
		$(this).parent().siblings('.transl')[0].classList.remove('active')
	};

	var show_translation = function(e) {
//      debugger;
		$(this)[0].classList.add('active')
		$(this).siblings('.btn-translate-orig')[0].classList.remove('active')

		$(this).parents('td.translatable')[0].classList.remove('blue')
		$(this).parents('td.translatable')[0].classList.remove('green')
		$(this).parents('td.translatable')[0].classList.add('green')

		$(this).parent().siblings('.text')[0].classList.remove('active')
		$(this).parent().siblings('.transl')[0].classList.add('active')
	};

	window.addTranslateClickHandlers = function() {
		$(".autoTransl").on("click", auto_translation);
		$('.editTransl').on("click", edit_translation);
		$('.submitTransl').on("click", submit_translation);
		$('.btn-translate-orig').on("click", show_original);
		$('.btn-translate-transl').on("click", show_translation);
	};

	addTranslateClickHandlers();

});
