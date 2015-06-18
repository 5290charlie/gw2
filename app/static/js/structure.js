jQuery(document).on('ready', function() {
    $('table.data-table').DataTable({
        'order': [
            [0, 'desc']
        ]
    });
});
