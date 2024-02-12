    // set the denomination of the currency
    const CURRENCY_LABEL = "&euro;" // "taler" , "\$", points

    let defaultHeadWidth = 0

    let elCashHolding = $('#cashHolding')
    let elCapLong = $('#capLong')

    let cashHolding = js_vars.cashHolding

    // set endowment table
    $(document).ready(function () {
        elCashHolding.html(cu(cashHolding))
        elCapLong.html(cu(elCapLong.html()))
        // for pages before results assetValues is undefined (for js) but should be visible in results
        if (typeof js_vars.assetValue !== 'undefined' && js_vars.assetValue !== null) {
            let elAssetsValue = $('#assetsValue')
            elAssetsValue.html(cu(elAssetsValue.html()))
        }
        $('#assetsValue tbody tr').filter(function() {
            return isNaN($(this).children('td').eq(0).attr('value'));
        }).html(`<td colSpan="2"> </td>`);

    })

    function cu(amount) {
        //return `&euro;${parseFloat(amount).toFixed(2)}`;
        let value = parseFloat(amount).toFixed(2)
        if (Number.isNaN(value))
        {
            return amount
        }
        return `${CURRENCY_LABEL}${value} `
    }
