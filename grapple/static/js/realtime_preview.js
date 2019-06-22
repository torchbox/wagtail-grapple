$(document).ready(() => {
    // Make existing wagtail code send form data to backend on KeyUp
    $('.action-preview').attr('data-auto-update', "true")

    // Trigger preview save on key up
    let $previewButton = $('.action-preview'), $form = $('#page-edit-form')
    let previewUrl = $previewButton.data('action')
    let autoUpdatePreviewDataTimeout = -1

    const setPreviewData = () => {
        return $.ajax({
            url: `${previewUrl}?realtime_preview=true`,
            method: 'GET',
            data: new FormData($form[0]),
            processData: false,
            contentType: false
        })
    }

    $previewButton.one('click', function () {
        if ($previewButton.data('auto-update')) {
            $form.on('change keyup DOMSubtreeModified', function () {
                clearTimeout(autoUpdatePreviewDataTimeout)
                autoUpdatePreviewDataTimeout = setTimeout(setPreviewData, 1100)
            }).trigger('change')
        }
    })
})