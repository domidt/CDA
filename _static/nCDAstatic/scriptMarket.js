
    let selID = undefined

    let elBestBidsTableBody = $('#bestBidsTable tbody')
    let elBestAsksTableBody = $('#bestAsksTable tbody')
    let elBidsTableBody = $('#bidsTable tbody')
    let elAsksTableBody = $('#asksTable tbody')
    let elTradesTableBody = $('#tradesTable tbody')
    let elNewsTable = $('#newsTable')

    let my_id = js_vars.id_in_group

    function newOption(value, text) {
                return $('<option/>', {
                    value: value,
                    text: text
                })
            }

    $(document).ready(function () {
        for (let i = 0; i < numAssets; i++) {
            $('#limitBidAssetID, #limitAskAssetID, #marketAssetID').append(newOption(i + 1, assetNames[i]));
        }
    })


    $('#marketAssetID').on('click', function() {
        $('#bidsTable tbody, #asksTable tbody').children('tr').hide()
        $('#bidsTable tbody tr, #asksTable tbody tr').filter(function() {
            return $(this).children('td').eq(2).attr('value') === $('#marketAssetID').val();
        }).show();
    }
    )


    // Highlight selected limit order in the order book (whether to accept or to delete)
    $('#bidsTable, #asksTable').on('click', 'tbody tr', function (data) {
        selID = $(this).attr('value')
        let makerIDSelected = $(this).attr('data-value')
        $('#bidsTable tbody tr, #asksTable tbody tr').addClass('btn-outline-primary').removeClass('btn-primary btn-danger')
        $('*[ data-value=' + my_id + ']').addClass('btn-outline-danger').removeClass('btn-outline-primary')
        if (makerIDSelected != my_id) {
            $(this).removeClass('btn-outline-primary')
            $(this).addClass('btn-primary')
        } else {
            $(this).removeClass('btn-outline-danger')
            $(this).addClass('btn-danger')
        }
    })

    // to close the window with information about missing inputs when orders are not correctly specified
    $('#errorBidOffer, #errorAskOffer, #errorBidMarket, #errorAskMarket, #errorBidCancel, #errorAskCancel').on('click', 'button', function () {
        $(this).parent().css('display', 'none')
    })

    function showNews(msg) {
        news_div.innerText = msg
        setTimeout(function () {
            news_div.innerText = ''
        }, 10000)
    }

    function trade_desc(seller_id) {
        if(seller_id == my_id) {
            return 'You sold '
        } else {
            return 'You bought '
        }
    }

    function market_start() {
        liveSend({'operationType': 'market_start'})
    }

    $(window).on ('load', function () {
        market_start ()
        defaultHeadWidth = $('#bidsTable th').eq(0).width()
    })

    function liveRecv(data) {
        // sanitise
        if (data === undefined) {
            return
        }
        // javascript destructuring assignment
        let {bids, asks, trades, cashHolding, assetsHolding, highcharts_series, news, bestAsks, bestBids} = data;

        elCashHolding.html(cu(cashHolding))
        elBestBidsTableBody.html(Object.entries(bestBids).map(e => `<tr id='bestBidassetID${e[0]}' value=${e[0]}><td value=${e[0]}> Sell ${assetNames[e[0]-1]} for </td><td value=${e[1]}>${cu(e[1])}</td></tr>`).join(''))
        elBestAsksTableBody.html(Object.entries(bestAsks).map(e => `<tr id='bestAskassetID${e[0]}' value=${e[0]}><td value=${e[0]}> Buy ${assetNames[e[0]-1]} for </td><td value=${e[1]}>${cu(e[1])}</td></tr>`).join(''))
        $('#bestBidsTable tbody tr, #bestAsksTable tbody tr').filter(function() {
            return isNaN($(this).children('td').eq(1).attr('value'));
        }).html(`<td colSpan="2"> No offers available </td>`);

        elAssetsHoldingBody.html(Object.entries(assetsHolding).map(e => `<tr id='holdingAssetID${e[0]}' value=${e[0]}><td value=${e[1]}>${e[1]}</td><td value=${e[0]}> of ${assetNames[e[0]-1]}</td></tr>`).join(''))
        //if ( cashHolding + capLong == 0) {
        //    elBidOffer.disabled = true;
        //}
        // value describes the offerID and data-value the makerID
        elBidsTableBody.html(bids.map(e => `<tr id='offerID${e[2]}' value=${e[2]} data-value=${e[3]} data-custom="1" data-model-name=${e[4]}><td value=${e[1]}>${e[1]} for </td><td value=${e[0]}>${cu(e[0])} of </td><td value=${e[4]}>${assetNames[e[4] - 1]}</td></tr>`).join(''))
        elAsksTableBody.html(asks.map(e => `<tr id='offerID${e[2]}' value=${e[2]} data-value=${e[3]} data-custom="0" data-model-name=${e[4]}><td value=${e[1]}>${e[1]} for </td><td value=${e[0]}>${cu(e[0])} of </td><td value=${e[4]}>${assetNames[e[4] - 1]}</td></tr>`).join(''))
        elTradesTableBody.html(trades.map(e => `<tr><td>${trade_desc(e[3])}&nbsp;</td><td value=${e[1]}> ${ e[1] } of&nbsp;</td><td value=${e[4]}>${assetNames[e[4] - 1]} for&nbsp;</td><td> ${ cu(e[0]) } </td></tr>`).join(''))
        elNewsTable.html(news.map(e => `<tr><td>${e[0]}</td></tr>`).join(''))

        // Select others' Bids and Asks after this update
        $('#bidsTable tbody tr, #asksTable tbody tr').addClass('btn-outline-primary')
        // Select the own Bids and Asks after this update
        $('*[ data-value=' + my_id + ']').addClass('btn-outline-danger').removeClass('btn-outline-primary')

        // Select the Bids as Asks previously selected after this update
        if (selID !== undefined){ // checks whether a row has been selected previously{
            let prevSelected = $('#offerID' + selID) // creates a list of objects with matching offerIDs (should be unique or undefined)
            if (prevSelected !== undefined && prevSelected.length != 0) {
                let makerIDSelected = prevSelected.attr('data-value')
                if (makerIDSelected != my_id) {
                    prevSelected.removeClass('btn-outline-primary')
                    prevSelected.addClass('btn-primary')
                }
                else {
                    prevSelected.removeClass('btn-outline-danger')
                    prevSelected.addClass('btn-danger')
                }
            }
        }

        // Updates width in Bids and Asks tables between columns
        updateTableWidth()

        redrawChart(highcharts_series)
    }

    function updateTableWidth() {
        // Asks Table
        let firstAskRow = $('#asksTable tbody td')
        let firstAskRowWidth = 0
        if (firstAskRow !== undefined && firstAskRow.length != 0) {
            firstAskRowWidth = firstAskRow.eq(0).width ()
        }
        let firstHeadAsk = $('#asksTable thead th')
        if (firstAskRowWidth != 0) {
            firstHeadAsk.eq(0).width(firstAskRowWidth)
        }
        else {
            firstHeadAsk.eq(0).width(defaultHeadWidth)
        }

        // Bids Table
        let firstBidRow = $('#bidsTable tbody td')
        let firstBidRowWidth = 0
        if (firstBidRow !== undefined && firstBidRow.length != 0) {
            firstBidRowWidth = firstBidRow.eq(0).width ()
        }
        let firstHeadBid = $('#bidsTable thead th')
        if (firstBidRowWidth != 0) {
            firstHeadBid.eq(0).width(firstBidRowWidth)
        }
        else {
            firstHeadBid.eq(0).width(defaultHeadWidth)
        }
    }

    // when a limit order is placed, they are first checked in the respective function and then send to the server where they are again checked
    function sendOffer(is_bid) {
        let errorField = (is_bid == 0) ? $('#errorAskOffer') : $('#errorBidOffer')
        let limitPrice = (is_bid == 0) ? $('#limitAskPrice').val() : $('#limitBidPrice').val()
        let limitVolume = (is_bid == 0) ? $('#limitAskVolume').val() : $('#limitBidVolume').val()
        let assetID = (is_bid == 0) ? $('#limitAskAssetID').val() : $('#limitBidAssetID').val()
        if (limitPrice == undefined || limitPrice <= 0 || assetID <= 0 ) {
            errorField.css("display", "inline-block")
            return // If you care about misspecified orders in your data, you may uncomment the return, it will be pushed back by the server
        }
        if (! checkVolume(errorField, limitVolume)) {
            return
        }
        liveSend({'operationType': 'limit_order', 'isBid': is_bid, 'limitPrice': limitPrice, 'limitVolume': limitVolume, 'assetID': assetID})
    }

    function checkVolume(errorField, Volume) {
        if (Volume == undefined || Volume <= 0 || !Number.isInteger(parseFloat(Volume))) {
            errorField.css("display", "inline-block")
            return false // If you care about misspecified orders in your data, you may uncomment the return
        }
        return true
    }

    // when
    function cancelLimit(is_bid) {
        let errorField = (is_bid == 0)? $('#errorAskCancel') : $('#errorBidCancel')
        let prevSelected = $('#offerID' + selID)
        let makerIDSelected = prevSelected.attr('data-value')
        if (! checkSelection(errorField, is_bid, prevSelected)) {
            return
        }
        if (makerIDSelected != my_id ) {
            errorField.css("display", "inline-block")
            return false // If you care about misspecified orders in your data, you may uncomment the return
        }
        let offerID = selID
        let limitPrice = prevSelected.children('td').eq(1).attr('value')
        liveSend({'operationType': 'cancel_limit', 'offerID': offerID, 'makerID': makerIDSelected, 'limitPrice': limitPrice, 'isBid': is_bid})
    }

    function checkSelection(errorField, is_bid, prevSelected) {
        if (selID === undefined) {
            errorField.css("display", "inline-block")
            return false // If you care about misspecified orders in your data, you may uncomment the return
        }
        if (prevSelected === undefined || prevSelected.length == 0) {
            errorField.css("display", "inline-block")
            return false // If you care about misspecified orders in your data, you may uncomment the return
        }
        let limitIsBidSelected = prevSelected.attr('data-custom')
        if (limitIsBidSelected != is_bid ) {
            errorField.css("display", "inline-block")
            return false // If you care about misspecified orders in your data, you may uncomment the return
        }
        return true
    }

    function sendAcc(is_bid) {
        let errorField = (is_bid == 0)? $('#errorAskMarket') : $('#errorBidMarket')
        let prevSelected = $('#offerID' + selID)
        let makerIDSelected = prevSelected.attr('data-value')
        let assetIDSelected = prevSelected.attr('data-model-name')
        if (! checkSelection(errorField, is_bid, prevSelected)) {
            return
        }
        if (makerIDSelected == my_id ) {
            errorField.css("display", "inline-block")
            return false // If you care about misspecified orders in your data, you may uncomment the return
        }
        let offerID = selID
        let transactionPrice = prevSelected.children('td').eq(1).attr('value')
        let transactionVolume = (is_bid == 0)? $('#transactionAskVolume').val() : $('#transactionBidVolume').val()
        if (! checkVolume(errorField, transactionVolume)){
            return
        }
        res = [ offerID, transactionPrice, transactionVolume ]
        if (res === undefined) {
            errorField.css("display", "inline-block")
            return
        }
        liveSend({'operationType': 'market_order', 'offerID': offerID, 'isBid': is_bid, 'transactionPrice': transactionPrice, 'transactionVolume': transactionVolume})
        $('#bidsTable tbody tr, #asksTable tbody tr').removeClass('btn-primary btn-outline-primary btn-danger btn-outline-danger')

    }