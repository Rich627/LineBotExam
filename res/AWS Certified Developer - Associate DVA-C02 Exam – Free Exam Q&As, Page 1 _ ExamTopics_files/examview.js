/* Hide & Show answers */
$('body').on('click', '.btn.reveal-solution', function (e) {
  e.preventDefault();
  let current_question_container = $(this).parent('.question-body');
  current_question_container.find('.question-answer').fadeIn(100);
  current_question_container.find('.hide-solution').removeClass('d-none');
  current_question_container.find('.most-voted-answer-badge').show();
  current_question_container.find('.correct-hidden').addClass('correct-choice');
  $(this).addClass('d-none');
});

$('body').on('click', '.btn.hide-solution', function (e) {
  e.preventDefault();
  let current_question_container = $(this).parent('.question-body');
  current_question_container.find('.question-answer').fadeOut(100);
  current_question_container.find('.reveal-solution').removeClass('d-none');
  current_question_container.find('.most-voted-answer-badge').hide();
  current_question_container.find('.correct-hidden').removeClass('correct-choice');
  $(this).addClass('d-none');
});

function is_question_mcq(question_jquery_object) {
  return question_jquery_object.find('.multi-choice-letter').length > 0;
}

function set_voting_configuration_by_question(question_jquery_object) {
  // Voted comments are only for MCQ questions, this function has nothing to do on other questions
  if (!is_question_mcq(question_jquery_object)) return;

  let choice_limit = question_jquery_object.find('.correct-answer').text().trim().length;
  let choices_elements = question_jquery_object.find('.multi-choice-letter');

  let choice_letters = '';
  choices_elements.each(function () {
    choice_letters += $(this).text().trim()[0];
  });

  let question_id = question_jquery_object
    .find('.question-body')
    .addBack('.question-body')
    .data('id');
  let discussion_object = getDiscussionObjectByQuestionId(question_id);

  set_voted_comment_config(discussion_object, choice_letters, choice_limit);
}

/* Open voting comment from inside a question */
$('body').on('click', '.vote-answer-button', function (e) {
  e.preventDefault();
  let question_container = $(this).closest('.question-body');
  let question_id = question_container.data('id');
  let discussion_object = getDiscussionObjectByQuestionId(question_id);
  if (discussion_object.length) {
    // This works for forum discussion page and inline discussions.
    set_voting_configuration_by_question(question_container);
    enable_voted_comment(discussion_object);
    $('html, body').animate({ scrollTop: discussion_object.offset().top - 150 });
  } else {
    // This is for modal discussions.
    resetDiscussionModal();
    loadDiscussionIntoModal(question_id, true);
    $('#discussion-modal').modal('show');
  }
});

/* Switch to voting comment from within a discussion */
$('body').on('click', '.switch-to-voting-comment-btn', function (e) {
  e.preventDefault();
  let question_id = $(this).closest('[data-discussion-question-id]').data('discussion-question-id');
  let question_container = $(`.question-body[data-id=${question_id}]`);
  set_voting_configuration_by_question(question_container);
  enable_voted_comment(getDiscussionObjectByQuestionId(question_id));
});

/* Switch back to simple comment from within a discussion */
$('body').on('click', '.switch-to-simple-comment-btn', function (e) {
  e.preventDefault();
  revert_to_simple_comment($(this).closest('.outer-discussion-container'));
});

function show_question_votes(question_jquery_objects) {
  question_jquery_objects.each(function (idx, question_object) {
    let vote_tally_str = $(question_object).find('.voted-answers-tally').text().trim();
    if (!vote_tally_str) {
      return;
    }
    let json_tally = JSON.parse(vote_tally_str);
    $(json_tally).each(function (idx, vote_data) {
      // This code adds the "Most Voted" badge after the choice that corresponds with that same letter\s.
      if (vote_data.is_most_voted) {
        for (let i = 0; i < vote_data.voted_answers.length; i++) {
          let letter = vote_data.voted_answers[i];
          let choice_object = $(question_object)
            .find(`.multi-choice-letter[data-choice-letter='${letter}']`)
            .parent();
          let most_voted_badge = $($('#most-voted-answer-badge-template').html()).hide();
          most_voted_badge.tooltip({ placement: 'right' });
          choice_object.append(most_voted_badge);
        }
      }
      //
      //Optional: Create a display for vote count for users to see
    });
  });
}

$(document).ready(function () {
  show_question_votes($('.question-body'));
});

function scrollToId(elementId) {
  window.scroll(0, findPos(document.getElementById(elementId)) - 100);
  function findPos(obj) {
    var curtop = 0;
    if (obj.offsetParent) {
      do {
        curtop += obj.offsetTop;
      } while ((obj = obj.offsetParent));
      return [curtop];
    }
  }
}

//This function receives a question jquery object and generates the stats bar/graph with the vote distribution.
// Either p1 or p2 can be the jQuery question object.
function show_community_votes(p1, p2) {
  let question_object;
  if (typeof p2 == 'undefined') question_object = $(p1);
  else question_object = $(p2);

  let tally_json_container = question_object.find('.voted-answers-tally');
  if (!tally_json_container.length) return; // No JSON data.

  let vote_stats_data = tally_json_container.text().trim();

  if (!vote_stats_data.length) return; // Empty data object (no votes)

  let vote_stats_json = JSON.parse(vote_stats_data);

  if (!vote_stats_json.length) return; // Empty votes object (no votes)

  let new_vote_stats_object = $($('.voting-distibution-template').html());
  let answer_area = question_object.find('.question-answer');

  let total_votes = vote_stats_json.map((i) => i.vote_count).reduce((a, b) => a + b);
  let percent_factor = 100 / total_votes;

  answer_area.append(new_vote_stats_object);
  question_object.find('.vote-bar').hide();
  let percent_coverage = 0;

  // Iterate over bars.
  for (var i = 0; i < vote_stats_json.length; i++) {
    let answer = vote_stats_json[i].voted_answers;
    let answer_vote_count = vote_stats_json[i].vote_count;
    let answer_vote_percent = Math.round(answer_vote_count * percent_factor);
    let correlating_bar = question_object.find('.vote-bar').eq(i);
    let text;
    let bar_width;

    // Choose if to show "other" in the last bar
    let is_last_bar = percent_coverage > 80 && i < vote_stats_json.length - 1;

    // We can accommodate no more than 4 distribution groups on the graph.
    is_last_bar = is_last_bar || i >= 3;

    if (is_last_bar) {
      text = 'Other';
      bar_width = 100 - percent_coverage;
    } else {
      text = `${answer} (${answer_vote_percent}%)`;
      bar_width = answer_vote_percent;
      correlating_bar.attr('title', `${answer_vote_count} votes.`);
    }

    if (bar_width < 15) {
      text = `${answer_vote_percent}%`;
      if (is_last_bar) correlating_bar.attr('title', text);
    }

    correlating_bar.text(text);

    correlating_bar.css('width', bar_width.toString() + '%');
    correlating_bar.show();

    percent_coverage += answer_vote_percent;

    if (is_last_bar) break;
  }
}

/*
    // Events for showing/hiding community votes distribution, currently disabled because it is always shown.
    $('body').on("mouseenter mouseover", ".voting-summary", function () {
        $(this).find(".vote-distribution-bar").slideDown({queue: false, duration: 200});
    });

    $('body').on("mouseleave", ".voting-summary", function () {
        $(this).find(".vote-distribution-bar").slideUp({queue: false, duration: 200});
    });

    $('body').on("click", ".voting-summary", function () {
        console.log("Leave");
        $(this).find(".vote-distribution-bar").slideToggle({queue: false, duration: 200});
    });
    */

$(document).ready(function () {
  $('.question-body').each(show_community_votes);
  $(function () {
    $('[data-toggle="tooltip"]').tooltip();
  });
});
