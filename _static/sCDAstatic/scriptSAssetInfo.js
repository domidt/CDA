    const COIN_LABEL = "&euro;"  // "taler" , "\$", points

    let elInformationBody = $('#information tbody')
    // set endowment table
    $(document).ready(function () {
        // for pages before results assetValues is undefined (for js) but should be visible in results
        if (typeof js_vars.assetValue !== 'undefined' && js_vars.assetValue !== null) {
            let elAssetsValue = $('#assetsValue')
            elAssetsValue.html(cu(elAssetsValue.html()))
        }
        // var information is sent to informed traders
        if (typeof js_vars.informed !== 'undefined' && js_vars.informed === true) {
            let information = js_vars.information
            elInformationBody.html(Object.entries(information).map(e => `<tr id='coin${e[0]}' value=${e[1][0]}><td value=${e[1][1]}>${e[1][1]} coins of &nbsp;</td><td value=${e[1][0]}>&nbsp; ${coin([e[1][0]])} </td><td>${coin(e[1][2])}</td></tr>`).join(''))
        }

        $('#assetsValue tbody tr, #information tbody tr').filter(function() {
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
