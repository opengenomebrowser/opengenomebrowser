data_table = genome_table.DataTable({
    rowId: 'identifier',
    scrollY: '250px',
    scrollCollapse: true,
    paging: true,
    select: {
        style: 'os'
    },
    "processing": true,
    "serverSide": true,
    pageLength: {{ default_page_length }},
    lengthMenu: [[-1, 10, 25, 50, 100, 200, 400, 800, 1600], ["All", 10, 25, 50, 100, 200, 400, 800, 1600]],
    // colReorder: true,
    "ajax": "{% url 'website:genome-table-ajax' %}",
    "createdRow": function (row, data, dataIndex) {
        if (data[{{ indexes.representative }}] == "False") {
            console.log(data[4], 'no-rep');
            $(row).addClass('no-representative');
        }
        if (data[{{ indexes.contaminated }}] == "True") {
            console.log(data[4], 'c');
            $(row).addClass('contaminated');
        }
        if (data[{{ indexes.organism_restricted }}] == "True") {
            console.log(data[4], 'r');
            $(row).addClass('restricted');
        }

        // add class for each "taxonomy"
        {% for tax_index in tax_indexes %}
            $('td', row).eq({{ tax_index.0 }}).attr('data-species', data[{{ tax_index.1 }}]);
        {% endfor %}
    },
    columnDefs: [
        {{ yadcf_column_defs|safe }}
    ]
});

yadcf.exFilterColumn(data_table, [
    {{ yadcf_ex_filter_column|safe }}
]);

yadcf.init(data_table, [
    {{ yadcf_init|safe }}
]);

var buttons = new $.fn.dataTable.Buttons(table, {
    // remove <div>-data from column titles (yadcf-workaround)
    // https://stackoverflow.com/questions/44048459/datatables-using-export-buttons-and-yadcf-causes-select-lists-to-be-exported
    buttons: [
        {
            extend: 'excel', text: 'Export to Excel',
            exportOptions: {
                format: {
                    header: function (data, row, column, node) {
                        var newdata = data;

                        newdata = newdata.replace(/<.*?<\/*?>/gi, '');
                        newdata = newdata.replace(/<div.*?<\/div>/gi, '');
                        newdata = newdata.replace(/<\/div.*?<\/div>/gi, '');
                        return newdata;
                    }
                }
            }
        },
        {
            extend: 'copy', text: 'Save to Clipboard',
            exportOptions: {
                format: {
                    header: function (data, row, column, node) {
                        var newdata = data;

                        newdata = newdata.replace(/<.*?<\/*?>/gi, '');
                        newdata = newdata.replace(/<div.*?<\/div>/gi, '');
                        newdata = newdata.replace(/<\/div.*?<\/div>/gi, '');
                        return newdata;
                    }
                }
            }
        }
    ]
}).container().appendTo($('#buttons'));

var all_colnames = [];
var visible_colnames = [];
data_table.init().columnDefs.forEach(function (item, index) {
    all_colnames.push(item['title']);
    if (item['bVisible'] != false) {
        visible_colnames.push(item['title'])
    }
});
