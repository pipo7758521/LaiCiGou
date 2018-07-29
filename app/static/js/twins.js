var app = new Vue({
    delimiters: ['${', '}'],
    el: '#app',
    data: {
        pages: 0,
        pageNo: 0,
        twins: []
    },
    created: function() {
        this.getPages();
        this.getTwins(1);
    },
    methods: {
        getPages: function() {
            var self = this;
            $.ajax({
                url: "getPages",
                type: "POST",
                dataType: 'json',
                data: {},
                async: true,
                success: function(data) {
                    self.pages = data.pages;
                    self.initPagination();
                },
                error: function() {
                    alert("getPages error");
                }
            });
        },
        initPagination: function() {
            var self = this;
            var obj = $('#pagination').twbsPagination({
                first: "首页",
                prev: "上一页",
                next: "下一页",
                last: "末页",
                totalPages: self.pages,
                visiblePages: 10,
                onPageClick: function(event, page) {
                    self.getTwins(page);
                }
            });
            console.info(obj.data());
        },
        getTwins: function(pageNo) {
            var self = this;
            $.ajax({
                url: "getTwins",
                type: "POST",
                dataType: 'json',
                data: {
                    pageNo: pageNo,
                },
                async: true,
                success: function(data) {
                    self.twins = data.documents;
                },
                error: function() {
                    alert("getTwins error");
                }
            });
        }
    }
})