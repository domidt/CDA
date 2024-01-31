
    let selID = undefined

    let elBidsTableBody = $('#bidsTable tbody')
    let elAsksTableBody = $('#asksTable tbody')
    let elNewsTable = $('#newsTable')

    let my_id = js_vars.id_in_group


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