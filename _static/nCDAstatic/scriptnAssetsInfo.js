    const COIN_LABEL = "&euro;"  // "taler" , "\$", points

    let elInformationBody = $('#information tbody')
    // set information table
    $(document).ready(function () {
        // var information is sent to informed traders
        if (typeof js_vars.informed !== 'undefined' && js_vars.informed === true) {
            let information = js_vars.information
            elInformationBody.html(information.map(e => `<tr id='$asset${e[0]}coin${e[1]}' value=${e[0]}><td value=${e[2]}>${assetNames[e[0] - 1]}:</td><td>${e[3]} coins of &nbsp;</td><td value=${e[2]}>&nbsp; ${coin([e[2]])} </td><td>${coin(e[4])}</td></tr>`).join(''))
        }

        $('#information tbody tr').filter(function() {
            return isNaN($(this).children('td').eq(0).attr('value'));
        }).html(`<td colSpan="2"> </td>`);

    })

    function coin(amount) {
        //return `&euro;${parseFloat(amount).toFixed(2)}`;
        let value = parseFloat(amount).toFixed(2)
        if (Number.isNaN(value))
        {
            return amount
        }
        return `${COIN_LABEL}${value}`
    }
