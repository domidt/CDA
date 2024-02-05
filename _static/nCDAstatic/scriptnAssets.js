    //  this script sets the fields that are not yet set by the general script
    let elAssetsHoldingBody = $('#assetsHoldings tbody')
    let elAssetValuesBody = $('#assetValues tbody')

    let assetNames = js_vars.assetNames
    let assetsHolding = js_vars.assetsHolding


    // set endowment table
    $(document).ready(function () {
        // for uninformed traders assetValues is undefined (for js) in stages before the result but should be visible in results
        elAssetsHoldingBody.html(Object.entries(assetsHolding).map(e => `<tr id='holdingAssetID${e[0]}' value=${e[0]}><td value=${e[1]}>${e[1]}</td><td value=${e[0]}> of ${assetNames[e[0] - 1]}</td></tr>`).join(''))

        if (typeof js_vars.assetValues !== 'undefined' && js_vars.assetValues !== null) {
            console.log('secondcheck', elAssetsHoldingBody)
            let assetValues = js_vars.assetValues
            elAssetValuesBody.html(Object.entries(assetValues).map(e => `<tr id='valueAssetID${e[0]}' value=${e[0]}><td value=${e[0]}>${assetNames[e[0] - 1]} is worth </td><td value=${e[1]}>${cu(e[1])}</td></tr>`).join(''))
        }
        if (typeof js_vars.allowShort !== 'undefined' && js_vars.allowShort === true) {
            let elCapShortBody = $('#capShort tbody')
            let capShort = js_vars.capShort
            elCapShortBody.html(Object.entries(capShort).map(e => `<tr id='ShortAssetID${e[0]}' value=${e[0]}><td value=${e[1]}>${e[1]}</td><td value=${e[0]}> of ${assetNames[e[0] - 1]}</td></tr>`).join(''))
        }
        if (typeof $('#initialEndowment') !== 'undefined') {
            let elInitialEndowment = $('#initialEndowment')
            let elEndEndowment = $('#endEndowment')
            let elTradingProfits = $('#tradingProfits')
            elInitialEndowment.html(cu(elInitialEndowment.html()))
            elEndEndowment.html(cu(elEndEndowment.html()))
            elTradingProfits.html(cu(elTradingProfits.html()))
        }

        $('#assetsValues tbody tr').filter(function() {
            return isNaN($(this).children('td').eq(1).attr('value'));
        }).html(`<td colSpan="2"> </td>`);

    })
