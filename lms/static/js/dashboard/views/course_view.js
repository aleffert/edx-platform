;(function (define) {
    'use strict';

    define(['jquery', 'backbone', 'underscore', 'logger'], function ($, Backbone, _, Logger) {
        var CourseView = Backbone.View.extend({

            events: {
                'click .action-more': 'toggleCourseActionsDropdown',
                'click .action-unenroll': 'unEnroll',
                'click .action-email-settings': 'emailSettings',
                'click #upgrade-to-verified': 'upgradeToVerified',
                'click #unregister_block_course': 'unRegisterBlockCourse'
            },

            initialize: function (options) {
                this.setElement(this.el);
                this.listenTo(options.tabbedView, 'rendered', this.rendered);
            },

            rendered: function () {
                var $actionUnroll = this.$('.action-unenroll');
                var $unRegisterBlockCourse = this.$('#unregister_block_course');

                this.bindUnEnrollModal($actionUnroll);
                this.bindUnEnrollModal($unRegisterBlockCourse);
                this.bindEmailSettingsModal();
            },

            bindUnEnrollModal: function ($selector) {
                $selector.leanModal({top: 120, overlay: 1, closeButton: ".close-modal", position: 'absolute'});
                var id = _.uniqueId('unenroll-');
                $selector.attr('id', id);

                // a bit of a hack, but gets the unique selector for the modal trigger
                var trigger = "#" + id;
                accessible_modal(
                    trigger,
                    "#unenroll-modal .close-modal",
                    "#unenroll-modal",
                    "#dashboard-main"
                );
            },

            bindEmailSettingsModal: function () {
                var $actionEmailSettings = this.$('.action-email-settings');
                $actionEmailSettings.leanModal({
                    top: 120,
                    overlay: 1,
                    closeButton: ".close-modal",
                    position: 'absolute'
                });

                var id = _.uniqueId('email-settings-');
                $actionEmailSettings.attr('id', id);
                // a bit of a hack, but gets the unique selector for the modal trigger
                var trigger = "#" + id;
                accessible_modal(
                    trigger,
                    "#email-settings-modal .close-modal",
                    "#email-settings-modal",
                    "#dashboard-main"
                );
            },

            toggleCourseActionsDropdown: function (e) {
                var index = this.$(e.currentTarget).data('dashboard-index');

                // Toggle the visibility control for the selected element and set the focus
                var dropDown = this.$('div#actions-dropdown-' + index);

                dropDown.toggleClass('is-visible');
                dropDown.hasClass('is-visible') ? dropDown.attr('tabindex', -1) : dropDown.removeAttr('tabindex');

                // Inform the ARIA framework that the dropdown has been expanded
                var anchor = this.$(e.currentTarget);
                var ariaExpandedState = (anchor.attr('aria-expanded') === 'true');
                anchor.attr('aria-expanded', !ariaExpandedState);

                // Suppress the actual click event from the browser
                e.preventDefault();
            },

            unEnroll: function (e) {

                var element = this.$(e.currentTarget);
                var track_info = element.data("track-info");
                var course_number = element.data("course-number");
                var course_name = element.data("course-name");
                var cert_name_long = element.data("cert-name-long");

                $('#track-info').html(interpolate(track_info, {
                    course_number: "<span id='unenroll_course_number'>" + course_number + "</span>",
                    course_name: "<span id='unenroll_course_name'>" + course_name + "</span>",
                    cert_name_long: "<span id='unenroll_cert_name'>" + cert_name_long + "</span>"
                }, true));

                $('#refund-info').html(element.data("refund-info"));
                $("#unenroll_course_id").val(element.data("course-id"));
            },

            emailSettings: function (e) {
                $("#email_settings_course_id").val(this.$(e.currentTarget).data("course-id"));
                $("#email_settings_course_number").text(this.$(e.currentTarget).data("course-number"));
                if (this.$(e.currentTarget).data("optout") === "False") {
                    $("#receive_emails").prop('checked', true);
                }
            },

            upgradeToVerified: function (e) {
                var user = this.$(e.currentTarget).closest(".action-upgrade").data("user");
                var course = this.$(e.currentTarget).closest(".action-upgrade").data("course-id");

                Logger.log('edx.course.enrollment.upgrade.clicked', [user, course], null);
            },

            unRegisterBlockCourse: function (e) {
                if (this.$('#block-course-msg').length) {
                    $('.disable-look-unregister').click();
                }
            }
        });

        return CourseView;
    });

}).call(this, define || RequireJS.define);
