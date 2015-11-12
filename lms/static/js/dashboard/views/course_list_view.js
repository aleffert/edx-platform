;(function (define) {
    'use strict';

    define(['jquery', 'common/js/components/views/list'], function ($, ListView) {

        var CourseListView = ListView.extend({

            initialize: function (options) {
                this.itemViewClass = options.itemViewClass || this.itemViewClass;
                this.template = options.template;
                this.parent = options.parent;

                this.itemViews = [];
            },

            render: function () {
                var self = this;

                this.$el.html($(this.template).html());
                this.$('.course').each(function () {
                    self.createItemView(this);
                });

                return this;
            },

            createItemView: function (element) {
                var itemView = new this.itemViewClass({
                    el: this.$(element).get(0),
                    tabbedView: this.parent
                });

                this.itemViews.push(itemView);
            }
        });

        return CourseListView;
    });

}).call(this, define || RequireJS.define);
