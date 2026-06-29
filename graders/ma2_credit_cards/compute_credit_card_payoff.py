# graders/credit_card/compute_credit_card_payoff.py

def compute_credit_card_payoff_months(
    balance: float,
    min_percent: float,
    fixed_min: float,
    apr_percent: float,
    payments_per_year: int
):
    """
    Computes the number of months required to pay off a credit card balance
    using the rules from the assignment:

        payment = MAX(fixed_min, min_percent * balance)
        new_balance = (balance - payment) * (1 + monthly_rate)

    Interest accrues AFTER payment.
    Payment is applied BEFORE interest.
    Interest compounds monthly.

    Returns the payoff month count (int).

    This loop is extremely light and runs in <0.0001 seconds.
    """

    # Convert APR to monthly decimal rate
    monthly_rate = (apr_percent / 100) / payments_per_year

    month = 0

    # We cap at 600 iterations just for safety (50 years)
    # but typical payoff is < 240 months.
    while balance > 0 and month < 600:
        month += 1

        # Compute payment for this month
        percent_payment = min_percent * balance
        payment = max(fixed_min, percent_payment)

        # Ensure we never pay more than the remaining balance
        payment = min(payment, balance)

        # Apply payment
        after_payment = balance - payment

        # Apply monthly interest (after payment)
        balance = after_payment * (1 + monthly_rate)

        # In last month balance may go slightly negative due to float behavior
        if balance < 0:
            balance = 0

    return month
