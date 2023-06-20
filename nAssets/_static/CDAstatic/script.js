    const CURRENCY_LABEL = "taler" // "&euro;", "\$", points

    let defaultHeadWidth = 0

    let elCashHolding = $('#cashHolding')
    let elAssetsHoldingBody = $('#assetsHoldings tbody')
    let elAssetsValuesBody = $('#assetsValues tbody')
    let elCapLongBody = $('#capLong')

    let assetNames = js_vars.assetNames
    let numAssets = js_vars.numAssets
    let cashHolding = js_vars.cashHolding
    let assetsHolding = js_vars.assetsHolding

    // set endowment table
    $(document).ready(function () {
        elCashHolding.html(cu(cashHolding))
        elCapLongBody.html(cu (elCapLongBody.html()))
        // assetValues is undefined (for js) in stages before the result
        if (typeof js_vars.assetValues !== 'undefined' && js_vars.assetValues !== null) {
            let assetValues = js_vars.assetValues
            elAssetsValuesBody.html(Object.entries(assetValues).map(e => `<tr id='assetID${e[0]}' value=${e[0]}><td value=${e[0]}>${assetNames[e[0] - 1]} is worth </td><td value=${e[1]}>${cu(e[1])}</td></tr>`).join(''))
        }
        // otherwise var information is sent to informed traders
        else if (typeof js_vars.informed !== 'undefined' && js_vars.informed === true) {
            let information = js_vars.information
            let informed = js_vars.informed
            elAssetsValuesBody.html(Object.entries(information).map(e => `<tr id='assetID${e[0]}' value=${e[0]}><td value=${e[0]}>${assetNames[e[0] - 1]} is worth </td><td value=${e[1]}>${cu(e[1])}</td></tr>`).join(''))
        }
        if (typeof js_vars.allowShort !== 'undefined' && js_vars.allowShort === true) {
            let elCapShortBody = $('#capShort tbody')
            let capShort = js_vars.capShort
            elCapShortBody.html(Object.entries(capShort).map(e => `<tr id='assetID${e[0]}' value=${e[0]}><td value=${e[1]}>${e[1]}</td><td value=${e[0]}> of ${assetNames[e[0] - 1]}</td></tr>`).join(''))
        }
        if (typeof $('#initialEndowment') !== 'undefined') {
            let elInitialEndowment = $('#initialEndowment')
            let elEndEndowment = $('#endEndowment')
            let elTradingProfits = $('#tradingProfits')
            elInitialEndowment.html(cu(elInitialEndowment.html()))
            elEndEndowment.html(cu(elEndEndowment.html()))
            elTradingProfits.html(cu(elTradingProfits.html()))
        }
        elAssetsHoldingBody.html(Object.entries(assetsHolding).map(e => `<tr id='holdingAssetID${e[0]}' value=${e[0]}><td value=${e[1]}>${e[1]}</td><td value=${e[0]}> of ${assetNames[e[0]-1]}</td></tr>`).join(''))
    })


    function cu(amount) {
        //return `&euro;${parseFloat(amount).toFixed(2)}`;
        let value = parseFloat(amount).toFixed(2)
        if (Number.isNaN(value))
        {
            return amount
        }
        return `${value} ${CURRENCY_LABEL}`
    }
