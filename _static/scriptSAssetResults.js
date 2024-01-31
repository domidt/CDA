    const CURRENCY_LABEL = "&euro;"// "taler" , "\$", points

    let defaultHeadWidth = 0

    let elAssetsHoldingBody = $('#assetsHoldings tbody')
    let elAssetsValuesBody = $('#assetsValues tbody')

    let assetsHolding = js_vars.assetsHolding

    // set endowment table
    $(document).ready(function () {
        // for pages before results assetValues is undefined (for js) but should be visible in results
        if (typeof js_vars.assetValue !== 'undefined' && js_vars.assetValue !== null) {
            let assetsValue = $('#assetsValue')
            elAssetsValuesBody.html(cu(elAssetsValue.html()))
        }
        if (typeof $('#initialEndowment') !== 'undefined') {
            let elInitialEndowment = $('#initialEndowment')
            let elEndEndowment = $('#endEndowment')
            let elTradingProfits = $('#tradingProfits')
            elInitialEndowment.html(cu(elInitialEndowment.html()))
            elEndEndowment.html(cu(elEndEndowment.html()))
            elTradingProfits.html(cu(elTradingProfits.html()))
        }

        $('#assetsValue tbody tr, #information tbody tr').filter(function() {
            return isNaN($(this).children('td').eq(0).attr('value'));
        }).html(`<td colSpan="2"> </td>`);

    })
