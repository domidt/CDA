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
