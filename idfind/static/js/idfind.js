
jQuery(document).ready(function() {    

    // clear the title from the front page search box
    if (jQuery('.frontin').val() == "") {
        jQuery('.frontin').val("/^(IDFind).*?$/");
    }
    var clearit = function(event) {
        if (jQuery(this).val() == "/^(IDFind).*?$/") {
            jQuery(this).val("");
        }
    }
    jQuery('.frontin').bind('focus',clearit);

    // search for collection id similar to that provided, and warn of duplicates controlled by third parties
    var checkcoll = function(event) {
        jQuery.ajax({
            url: '/collections.json?q=id:"' + jQuery(this).val() + '"'
            , type: 'GET'
            , success: function(json, statusText, xhr) {
                if (json.records.length != 0) {
                    if (json.records[0]['owner'] != jQuery('#current_user').val()) {
                        if (jQuery('#collwarning').length == 0) {
                            var where = json.records[0]['owner'] + '/' + json.records[0]['id']
                            jQuery('#collection').after('&nbsp;&nbsp;<span id="collwarning" class="label warning"><a href="/' + where + '">sorry, in use</a>. Please change.</span>');
                        }
                    }
                } else {
                    jQuery('#collwarning').remove();
                }
            }
            , error: function(xhr, message, error) {
            }
        });
        
    }
    jQuery('#collection').bind('keyup',checkcoll);
	
});


