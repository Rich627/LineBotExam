// Comments include validation:
$(document).ready(function() {
    if (!$('#report-comment-modal').length) {
        alert("Comment system is missing its report modal.")
    }
});

// Handle collapse & expand comments
$('body').on('click', '.comment-toggle', function(e){
    e.preventDefault();
    var comment = $(this).closest('.comment-container');
    comment.find('.comment-body:first').slideToggle();
    comment.find('.media-body > .comment-ellipsis').toggle();
    comment.find('> .comment-toggle').toggle();
});


// Handle comment reply show
$('body').on('click', '.comment-reply-to', function(e){
    e.preventDefault();

    // We need to revert the root new-comment to a simple comment in-order to clone it.
    // this is not very elegant but will do for now.
    let discussion_jq_object = $(this).closest(".outer-discussion-container");
    revert_to_simple_comment(discussion_jq_object);

    if (!isUserLoggedIn()) {$('#login-required-comment-modal').modal('show'); return} // Validate logged-in user

    var reply_placeholder = $(this).closest('.comment-container').find('.new-comment-box-container:first');

    //Is the reply placeholder already occupied?
    if (reply_placeholder.html().trim().length > 0)
        return;

    var reply_box_template = $($(this).closest('.comments-container').find('> .create-comment-base .new-comment-box').clone());
    reply_placeholder.append(reply_box_template);

    reply_box_template.find('textarea').val(''); // Reset the new text area

    // Set the reply-to attribute for the new comment box:
    var comment_id = getCommentIdByElement(reply_placeholder);
    reply_box_template.attr('data-reply-to', comment_id);
    reply_box_template.find('.comment-submit-button').removeAttr("disabled").removeClass("disabled").html("Submit");
    reply_box_template.find(".non-voting-comment-box").remove();
    reply_box_template.show();
});


// Handle comment reply cancel button
$('body').on('click', '.comment-cancel-button', function(e){
    e.preventDefault();
    $(this).closest('.new-comment-box').remove();
});


// Submit/Reply button handler:
$('body').on('click', '.comment-submit-button', function(e){
    e.preventDefault();

    if (!isUserLoggedIn()) {$('#login-required-comment-modal').modal('show'); return} // Validate logged-in user

    let new_comment_box = $(this).closest('.new-comment-box');
    let is_voting_comment = Boolean(new_comment_box.attr("data-vote-comment"));

    if (is_voting_comment) {
        let marked_checkboxes = new_comment_box.find('.vote-checkboxes input:checked');
        if (!marked_checkboxes.length) {
            bootbox.alert("Please mark at least one of the answers or switch to a simple comment.");
            return
        }
        var selected_answers = "";
        marked_checkboxes.each(function(idx, checkbox) {
            selected_answers += $(checkbox).attr("value");
        })
    }

    $(this).addClass('disabled').attr('disabled','disabled').text('Submitting...');
    $('.awaiting-reply').removeClass('awaiting-reply');

    var comment_replies_container = new_comment_box.closest('.comment-container').find('.comment-replies:first');
    if (!comment_replies_container.length)
        comment_replies_container = $(this).closest('.comments-container').find('.discussion-container');
    comment_replies_container.addClass('awaiting-reply')
    var data = getDataAttributes(new_comment_box[0]);
    var comment_content = $(this).closest('.new-comment-box').find('textarea').val();
    data['comment-content']=comment_content;

    if (is_voting_comment)
        data['selected-answers']=selected_answers;

    //Start server submission here...
    $.ajax({
        url: '/ajax/discussion/comment/new',
        data: data,
        success: function(result, status) {
            // Generate the new reply body and add it:
            var new_reply = $(result);
            reply_destination = $('.awaiting-reply');
            new_reply.hide();
            reply_destination.prepend(new_reply);
            new_reply.fadeIn();
            // Discard the "new comment" box
            reply_destination.closest('.comment-container').find('.comment-cancel-button').click();
            new_comment_box.hide();
        },
        error: function error(xhr,status,error) {
            // Show error to the user:
            bootbox.alert(xhr.responseText);
            // Return the submit button back to normal:
            $('.comment-submit-button[disabled=disabled]').attr('disabled','').removeClass('disabled').text('Submit');
        }
    });
});

// ** BEGIN UPVOTE HANDLING

// Handle upvote on comment.
$('body').on('click', '.comment-upvote', function(e){
    e.preventDefault();
    if (!isUserLoggedIn()) {$('#login-required-comment-modal').modal('show'); return} // Validate logged-in user
    $(this).addClass('disabled').attr('disabled','disabled');
    var comment_id = getCommentIdByElement(this);
    var csrf_value = getCSRFTokenValue();
    var data = {'csrfmiddlewaretoken': csrf_value};
    var url = '/ajax/discussion/comment/'+comment_id+'/upvote';
    $('.upvote-target').removeClass('upvote-target');
    $(this).closest('.comment-control').find('.upvote-count').addClass('upvote-target');
    $.ajax({
        url: url,
        type: 'post',
        data: data,
        success: function (result, status) {
            $('.upvote-target').text(parseInt($('.upvote-target').text())+1).addClass('font-weight-bold');
        },
        error: function error(xhr,status,error) {
            $('.upvote-target').closest('.comment-control').find('.comment-control-error').text(xhr.responseText);
        }
    });
});

// ** END UPVOTE HANDLING


//  ** BEGIN Report comment handling

// Report button handle:
$('body').on('click', '.comment-flag-report', function(e){
    e.preventDefault();
    var comment_id = $(this).closest('.comment-container').attr('data-comment-id');
    var comment_username = $(this).closest('.comment-container').find('.comment-username:first').text();
    $("#report-comment-modal .comment-report-modal-username").text(comment_username);
    $("#report-comment-modal").attr('data-comment-id', comment_id);
    $("#report-comment-modal").modal('show');
});

// Modal confirm handler and callback setter
function reportCommentConfirm(callback){
  $("#modal-btn-yes").on("click", function(){
    callback(true);
    $("#report-comment-modal").modal('hide');
  });

  $("#report-comment-modal").on("click", function(){
    $("#report-comment-modal").modal('hide');
  });
};

// Set the callback on the confirm dialog
reportCommentConfirm(function(confirmed){
    if (confirmed) {
        var comment_id = $("#report-comment-modal").attr('data-comment-id');
        var csrf_value = getCSRFTokenValue();
        var data = {'csrfmiddlewaretoken': csrf_value};
        var url = '/ajax/discussion/comment/'+comment_id+'/report';
        $.ajax({
            url: url,
            type: 'post',
            data: data,
            success: function (result, status) {
                alert(result);
            },
            error: function error(xhr,status,error) {
                alert(xhr.responseText);
            }
        });
    }
});

// ** END Report comments handling


/* START Answer vote mechanism */

function set_voted_comment_config(discussion_container_jquery_object, choices, limit){
    // Create new checkboxes:
    let root_vote_box = discussion_container_jquery_object.find(".choice-vote-box");
    let checkbox_container = root_vote_box.find('.vote-checkboxes').first();
    checkbox_container.empty();
    for (let i = 0; i < choices.length; i++) {
        checkbox_container.append(`<input id="answer_${choices[i]}" type="checkbox" value="${choices[i]}"><label for="answer_${choices[i]}">${choices[i]}</label>`);
    }

    // Limit the checkbox "checked" count.
    root_vote_box.find('input').on('change', function(evt) {
        if($(this).siblings(':checked').length >= limit) {
            this.checked = false;
        }
    });

    init_voting_tooltip();
    // Mark that the discussion has a configured voting settings.
    discussion_container_jquery_object.find(".non-voting-comment-box").addClass("configured").show();
}

function enable_voted_comment(discussion_container_jquery_object) {
    if (!discussion_container_jquery_object) {
        discussion_container_jquery_object = $(this).closest(".outer-discussion-container");
    }
    discussion_container_jquery_object.find(".choice-vote-box").first().show();
    $(".non-voting-comment-box").hide();
    // Change the placeholder and mark the new-comment as a voting comment:
    discussion_container_jquery_object.find(".new-comment-textarea").first().attr("placeholder", "Please explain your answer").closest(".new-comment-box").attr("data-vote-comment", 1);
}


function init_voting_tooltip() {
    $(".voting-comment-questionmark").tooltip(
        {
            html: true,
            title: $('#voting-comment-tooltip').html(),
            placement: 'right'
        });
}

function revert_to_simple_comment(discussion_jquery_object){
    discussion_jquery_object.find(".choice-vote-box").hide();
    discussion_jquery_object.find(".non-voting-comment-box.configured").show();
    discussion_jquery_object.find(".new-comment-textarea").attr("placeholder", "Type your comment...").closest(".new-comment-box").removeAttr("data-vote-comment");
}

/* END Answer vote mechanism */


// ==== Utility functions
function getDataAttributes ( node ) {
    var i,
        attributeNodes = node.attributes,
        length = attributeNodes.length,
        attrs = {};

    for ( i = 0; i < length; i++ )
        if (attributeNodes[i].name.startsWith('data-'))
            attrs[attributeNodes[i].name.replace('data-','')] = attributeNodes[i].value;
    return attrs;
}

function getCommentIdByElement(element) {
    return $(element).closest('.comment-container').attr('data-comment-id');
}

function getCSRFTokenValue() {
    return $('.csrf-value').val();
}

function isUserLoggedIn() {
    return parseInt($('.is-logged-in').val());
}

function getDiscussionObjectByQuestionId(question_id){
    return $(`[data-discussion-question-id=${question_id}]`).find(".outer-discussion-container");
}

function getQuestionObjectByQuestionId(question_id){
    return $(`.question-body[data-id=${question_id}]`);
}