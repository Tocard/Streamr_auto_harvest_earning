from web3 import Web3
from web3.middleware import geth_poa_middleware
import logging

from vault import get_privkey_from_vault


def transform_sponsorships_array(sponsorships: list) -> list:

    checksum_sponsorship = []
    for sponsorship in sponsorships:
        checksum_sponsorship.append(Web3.to_checksum_address(sponsorship))
    return checksum_sponsorship


def have_enough_fund(web3: Web3, wallet_address: str) -> bool:
    if web3.is_connected():
        balance = web3.eth.get_balance(wallet_address)
    humanized_balance = balance / 10 ** 18
    if 0.5 < humanized_balance < 1:
        logging.warning("Balance: {} is enough but you should consider about getting more MATIC on wallet.".format(humanized_balance))
    elif humanized_balance > 1:
        logging.info("Enough Balance {} to claim".format(humanized_balance))
    else:
        logging.error("Balance: {} is low, not gonna claim anything".format(humanized_balance))
        return False
    return True


def run_harvest_process(web3, cfg: dict, contract, account, wallet_private_key: str):
    sponsorship_addresses = transform_sponsorships_array(cfg['sponsorship_to_claim'])
    gas_estimate = contract.functions.withdrawEarningsFromSponsorships(sponsorship_addresses).estimate_gas({
        'from': account.address,
    })
    gas_limit = int(gas_estimate * 1.5)
    current_gas_price = web3.eth.gas_price
    gas_price = int(current_gas_price * 1.2)
    logging.info("gas limit is set to {}, with current_gas_price to {} which will result into {} gas price".format(gas_limit / 10 ** 18, current_gas_price / 10 ** 18, gas_price / 10 ** 18))
    transaction = contract.functions.withdrawEarningsFromSponsorships(sponsorship_addresses).build_transaction({
        'from': account.address,
        'gas': gas_limit,
        'gasPrice': gas_price,
        'nonce': web3.eth.get_transaction_count(account.address),
    })
    signed_transaction = web3.eth.account.sign_transaction(transaction, wallet_private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_transaction.rawTransaction)
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    gas_used = receipt['gasUsed']
    logging.info("Transaction Hash: {}, Gas Used: {}".format(tx_hash.hex(), gas_used / 10 ** 18))


def collect_earning(cfg: dict):
    polygon_rpc_url = cfg['rpc_url']
    if cfg['vault_enabled']:
        wallet_private_key = get_privkey_from_vault(cfg)
    else:
        wallet_private_key = cfg['wallet_privkey']
    contract_address = cfg['operator_contract_adress']

    web3 = Web3(Web3.HTTPProvider(polygon_rpc_url))
    web3.middleware_onion.inject(geth_poa_middleware, layer=0)

    contract_abi = [{"inputs": [], "stateMutability": "nonpayable", "type": "constructor"},
                    {"inputs": [], "name": "AccessDenied", "type": "error"},
                    {"inputs": [], "name": "AccessDeniedDATATokenOnly", "type": "error"},
                    {"inputs": [], "name": "AccessDeniedNodesOnly", "type": "error"},
                    {"inputs": [], "name": "AccessDeniedOperatorOnly", "type": "error"},
                    {"inputs": [], "name": "AccessDeniedStreamrSponsorshipOnly", "type": "error"}, {
                        "inputs": [{"internalType": "uint256", "name": "operatorTokenBalanceWei", "type": "uint256"},
                                   {"internalType": "uint256", "name": "minimumDelegationWei", "type": "uint256"}],
                        "name": "DelegationBelowMinimum", "type": "error"},
                    {"inputs": [], "name": "DidNotReceiveReward", "type": "error"},
                    {"inputs": [], "name": "FirstEmptyQueueThenStake", "type": "error"},
                    {"inputs": [{"internalType": "uint256", "name": "newOperatorsCutFraction", "type": "uint256"}],
                     "name": "InvalidOperatorsCut", "type": "error"}, {
                        "inputs": [{"internalType": "address", "name": "module", "type": "address"},
                                   {"internalType": "bytes", "name": "data", "type": "bytes"}], "name": "ModuleCallError",
                        "type": "error"},
                    {"inputs": [{"internalType": "bytes", "name": "data", "type": "bytes"}], "name": "ModuleGetError",
                     "type": "error"}, {"inputs": [], "name": "NoEarnings", "type": "error"},
                    {"inputs": [], "name": "NotMyStakedSponsorship", "type": "error"}, {
                        "inputs": [{"internalType": "uint256", "name": "operatorBalanceWei", "type": "uint256"},
                                   {"internalType": "uint256", "name": "minimumSelfDelegationWei", "type": "uint256"}],
                        "name": "SelfDelegationTooLow", "type": "error"},
                    {"inputs": [], "name": "StakedInSponsorships", "type": "error"},
                    {"inputs": [], "name": "ZeroUndelegation", "type": "error"}, {"anonymous": False, "inputs": [
            {"indexed": True, "internalType": "address", "name": "owner", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "spender", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "value", "type": "uint256"}], "name": "Approval",
                                                                                  "type": "event"}, {"anonymous": False,
                                                                                                     "inputs": [
                                                                                                         {"indexed": True,
                                                                                                          "internalType": "address",
                                                                                                          "name": "delegator",
                                                                                                          "type": "address"},
                                                                                                         {"indexed": False,
                                                                                                          "internalType": "uint256",
                                                                                                          "name": "balanceWei",
                                                                                                          "type": "uint256"},
                                                                                                         {"indexed": False,
                                                                                                          "internalType": "uint256",
                                                                                                          "name": "totalSupplyWei",
                                                                                                          "type": "uint256"},
                                                                                                         {"indexed": False,
                                                                                                          "internalType": "uint256",
                                                                                                          "name": "dataValueWithoutEarnings",
                                                                                                          "type": "uint256"}],
                                                                                                     "name": "BalanceUpdate",
                                                                                                     "type": "event"},
                    {"anonymous": False,
                     "inputs": [{"indexed": True, "internalType": "address", "name": "delegator", "type": "address"},
                                {"indexed": False, "internalType": "uint256", "name": "amountDataWei", "type": "uint256"}],
                     "name": "Delegated", "type": "event"}, {"anonymous": False, "inputs": [
            {"indexed": True, "internalType": "address", "name": "nodeAddress", "type": "address"},
            {"indexed": False, "internalType": "string", "name": "jsonData", "type": "string"}], "name": "Heartbeat",
                                                             "type": "event"}, {"anonymous": False, "inputs": [
            {"indexed": False, "internalType": "uint8", "name": "version", "type": "uint8"}], "name": "Initialized",
                                                                                "type": "event"}, {"anonymous": False,
                                                                                                   "inputs": [
                                                                                                       {"indexed": False,
                                                                                                        "internalType": "uint256",
                                                                                                        "name": "valueDecreaseWei",
                                                                                                        "type": "uint256"}],
                                                                                                   "name": "Loss",
                                                                                                   "type": "event"},
                    {"anonymous": False, "inputs": [
                        {"indexed": False, "internalType": "string", "name": "metadataJsonString", "type": "string"},
                        {"indexed": True, "internalType": "address", "name": "operatorAddress", "type": "address"},
                        {"indexed": True, "internalType": "uint256", "name": "operatorsCutFraction", "type": "uint256"}],
                     "name": "MetadataUpdated", "type": "event"}, {"anonymous": False, "inputs": [
            {"indexed": False, "internalType": "address[]", "name": "nodes", "type": "address[]"}], "name": "NodesSet",
                                                                   "type": "event"}, {"anonymous": False, "inputs": [
            {"indexed": False, "internalType": "uint256", "name": "slashingAmountDataWei", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "slashingAmountInOperatorTokensWei", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "actuallySlashedInOperatorTokensWei", "type": "uint256"}],
                                                                                      "name": "OperatorSlashed",
                                                                                      "type": "event"}, {"anonymous": False,
                                                                                                         "inputs": [{
                                                                                                                        "indexed": False,
                                                                                                                        "internalType": "uint256",
                                                                                                                        "name": "totalStakeInSponsorshipsWei",
                                                                                                                        "type": "uint256"},
                                                                                                                    {
                                                                                                                        "indexed": False,
                                                                                                                        "internalType": "uint256",
                                                                                                                        "name": "dataTokenBalanceWei",
                                                                                                                        "type": "uint256"}],
                                                                                                         "name": "OperatorValueUpdate",
                                                                                                         "type": "event"},
                    {"anonymous": False, "inputs": [
                        {"indexed": False, "internalType": "uint256", "name": "valueIncreaseWei", "type": "uint256"},
                        {"indexed": True, "internalType": "uint256", "name": "operatorsCutDataWei", "type": "uint256"},
                        {"indexed": True, "internalType": "uint256", "name": "protocolFeeDataWei", "type": "uint256"}],
                     "name": "Profit", "type": "event"}, {"anonymous": False, "inputs": [
            {"indexed": True, "internalType": "address", "name": "delegator", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "amountWei", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "queueIndex", "type": "uint256"}], "name": "QueueUpdated",
                                                          "type": "event"}, {"anonymous": False, "inputs": [
            {"indexed": True, "internalType": "address", "name": "delegator", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "amountWei", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "queueIndex", "type": "uint256"}],
                                                                             "name": "QueuedDataPayout", "type": "event"},
                    {"anonymous": False, "inputs": [
                        {"indexed": True, "internalType": "contract Sponsorship", "name": "sponsorship", "type": "address"},
                        {"indexed": True, "internalType": "address", "name": "targetOperator", "type": "address"},
                        {"indexed": False, "internalType": "uint256", "name": "voteStartTimestamp", "type": "uint256"},
                        {"indexed": False, "internalType": "uint256", "name": "voteEndTimestamp", "type": "uint256"},
                        {"indexed": False, "internalType": "string", "name": "flagMetadata", "type": "string"}],
                     "name": "ReviewRequest", "type": "event"}, {"anonymous": False, "inputs": [
            {"indexed": True, "internalType": "bytes32", "name": "role", "type": "bytes32"},
            {"indexed": True, "internalType": "bytes32", "name": "previousAdminRole", "type": "bytes32"},
            {"indexed": True, "internalType": "bytes32", "name": "newAdminRole", "type": "bytes32"}],
                                                                 "name": "RoleAdminChanged", "type": "event"},
                    {"anonymous": False,
                     "inputs": [{"indexed": True, "internalType": "bytes32", "name": "role", "type": "bytes32"},
                                {"indexed": True, "internalType": "address", "name": "account", "type": "address"},
                                {"indexed": True, "internalType": "address", "name": "sender", "type": "address"}],
                     "name": "RoleGranted", "type": "event"}, {"anonymous": False, "inputs": [
            {"indexed": True, "internalType": "bytes32", "name": "role", "type": "bytes32"},
            {"indexed": True, "internalType": "address", "name": "account", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "sender", "type": "address"}], "name": "RoleRevoked",
                                                               "type": "event"}, {"anonymous": False, "inputs": [
            {"indexed": True, "internalType": "contract Sponsorship", "name": "sponsorship", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "stakedWei", "type": "uint256"}], "name": "StakeUpdate",
                                                                                  "type": "event"}, {"anonymous": False,
                                                                                                     "inputs": [
                                                                                                         {"indexed": True,
                                                                                                          "internalType": "contract Sponsorship",
                                                                                                          "name": "sponsorship",
                                                                                                          "type": "address"}],
                                                                                                     "name": "Staked",
                                                                                                     "type": "event"},
                    {"anonymous": False,
                     "inputs": [{"indexed": True, "internalType": "address", "name": "from", "type": "address"},
                                {"indexed": True, "internalType": "address", "name": "to", "type": "address"},
                                {"indexed": False, "internalType": "uint256", "name": "value", "type": "uint256"}],
                     "name": "Transfer", "type": "event"}, {"anonymous": False, "inputs": [
            {"indexed": True, "internalType": "address", "name": "delegator", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "amountDataWei", "type": "uint256"}],
                                                            "name": "Undelegated", "type": "event"}, {"anonymous": False,
                                                                                                      "inputs": [
                                                                                                          {"indexed": True,
                                                                                                           "internalType": "contract Sponsorship",
                                                                                                           "name": "sponsorship",
                                                                                                           "type": "address"}],
                                                                                                      "name": "Unstaked",
                                                                                                      "type": "event"},
                    {"stateMutability": "nonpayable", "type": "fallback"}, {"inputs": [], "name": "CONTROLLER_ROLE",
                                                                            "outputs": [
                                                                                {"internalType": "bytes32", "name": "",
                                                                                 "type": "bytes32"}],
                                                                            "stateMutability": "view", "type": "function"},
                    {"inputs": [], "name": "DEFAULT_ADMIN_ROLE",
                     "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}], "stateMutability": "view",
                     "type": "function"}, {"inputs": [], "name": "OWNER_ROLE",
                                           "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
                                           "stateMutability": "view", "type": "function"}, {
                        "inputs": [{"internalType": "address", "name": "owner", "type": "address"},
                                   {"internalType": "address", "name": "spender", "type": "address"}], "name": "allowance",
                        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view",
                        "type": "function"}, {"inputs": [{"internalType": "address", "name": "spender", "type": "address"},
                                                         {"internalType": "uint256", "name": "amount", "type": "uint256"}],
                                              "name": "approve",
                                              "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
                                              "stateMutability": "nonpayable", "type": "function"},
                    {"inputs": [{"internalType": "address", "name": "delegator", "type": "address"}],
                     "name": "balanceInData",
                     "outputs": [{"internalType": "uint256", "name": "amountDataWei", "type": "uint256"}],
                     "stateMutability": "view", "type": "function"},
                    {"inputs": [{"internalType": "address", "name": "account", "type": "address"}], "name": "balanceOf",
                     "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view",
                     "type": "function"},
                    {"inputs": [], "name": "decimals", "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
                     "stateMutability": "view", "type": "function"}, {
                        "inputs": [{"internalType": "address", "name": "spender", "type": "address"},
                                   {"internalType": "uint256", "name": "subtractedValue", "type": "uint256"}],
                        "name": "decreaseAllowance", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
                        "stateMutability": "nonpayable", "type": "function"},
                    {"inputs": [{"internalType": "uint256", "name": "amountWei", "type": "uint256"}], "name": "delegate",
                     "outputs": [], "stateMutability": "nonpayable", "type": "function"},
                    {"inputs": [], "name": "delegationPolicy",
                     "outputs": [{"internalType": "contract IDelegationPolicy", "name": "", "type": "address"}],
                     "stateMutability": "view", "type": "function"}, {"inputs": [], "name": "exchangeRatePolicy",
                                                                      "outputs": [
                                                                          {"internalType": "contract IExchangeRatePolicy",
                                                                           "name": "", "type": "address"}],
                                                                      "stateMutability": "view", "type": "function"}, {
                        "inputs": [{"internalType": "contract Sponsorship", "name": "sponsorship", "type": "address"},
                                   {"internalType": "address", "name": "targetOperator", "type": "address"},
                                   {"internalType": "string", "name": "flagMetadata", "type": "string"}], "name": "flag",
                        "outputs": [], "stateMutability": "nonpayable", "type": "function"}, {
                        "inputs": [{"internalType": "contract Sponsorship", "name": "sponsorship", "type": "address"},
                                   {"internalType": "uint256", "name": "maxQueuePayoutIterations", "type": "uint256"}],
                        "name": "forceUnstake", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
                    {"inputs": [], "name": "getNodeAddresses",
                     "outputs": [{"internalType": "address[]", "name": "", "type": "address[]"}], "stateMutability": "view",
                     "type": "function"},
                    {"inputs": [{"internalType": "bytes32", "name": "role", "type": "bytes32"}], "name": "getRoleAdmin",
                     "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}], "stateMutability": "view",
                     "type": "function"}, {"inputs": [], "name": "getSponsorshipsAndEarnings", "outputs": [
            {"internalType": "address[]", "name": "addresses", "type": "address[]"},
            {"internalType": "uint256[]", "name": "earnings", "type": "uint256[]"},
            {"internalType": "uint256", "name": "maxAllowedEarnings", "type": "uint256"}], "stateMutability": "view",
                                           "type": "function"}, {"inputs": [], "name": "getStreamMetadata", "outputs": [
            {"internalType": "string", "name": "", "type": "string"}], "stateMutability": "view", "type": "function"}, {
                        "inputs": [{"internalType": "bytes32", "name": "role", "type": "bytes32"},
                                   {"internalType": "address", "name": "account", "type": "address"}], "name": "grantRole",
                        "outputs": [], "stateMutability": "nonpayable", "type": "function"}, {
                        "inputs": [{"internalType": "bytes32", "name": "role", "type": "bytes32"},
                                   {"internalType": "address", "name": "account", "type": "address"}], "name": "hasRole",
                        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}], "stateMutability": "view",
                        "type": "function"},
                    {"inputs": [{"internalType": "string", "name": "jsonData", "type": "string"}], "name": "heartbeat",
                     "outputs": [], "stateMutability": "nonpayable", "type": "function"}, {
                        "inputs": [{"internalType": "address", "name": "spender", "type": "address"},
                                   {"internalType": "uint256", "name": "addedValue", "type": "uint256"}],
                        "name": "increaseAllowance", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
                        "stateMutability": "nonpayable", "type": "function"},
                    {"inputs": [{"internalType": "contract Sponsorship", "name": "", "type": "address"}],
                     "name": "indexOfSponsorships", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                     "stateMutability": "view", "type": "function"}, {
                        "inputs": [{"internalType": "address", "name": "tokenAddress", "type": "address"},
                                   {"internalType": "contract StreamrConfig", "name": "config", "type": "address"},
                                   {"internalType": "address", "name": "ownerAddress", "type": "address"},
                                   {"internalType": "string", "name": "operatorTokenName", "type": "string"},
                                   {"internalType": "string", "name": "operatorMetadataJson", "type": "string"},
                                   {"internalType": "uint256", "name": "operatorsCut", "type": "uint256"},
                                   {"internalType": "address[3]", "name": "modules", "type": "address[3]"}],
                        "name": "initialize", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
                    {"inputs": [{"internalType": "address", "name": "forwarder", "type": "address"}],
                     "name": "isTrustedForwarder", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
                     "stateMutability": "view", "type": "function"}, {"inputs": [], "name": "metadata", "outputs": [
            {"internalType": "string", "name": "", "type": "string"}], "stateMutability": "view", "type": "function"},
                    {"inputs": [], "name": "name", "outputs": [{"internalType": "string", "name": "", "type": "string"}],
                     "stateMutability": "view", "type": "function"},
                    {"inputs": [{"internalType": "address", "name": "", "type": "address"}], "name": "nodeIndex",
                     "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view",
                     "type": "function"}, {"inputs": [], "name": "nodeModule", "outputs": [
            {"internalType": "contract INodeModule", "name": "", "type": "address"}], "stateMutability": "view",
                                           "type": "function"},
                    {"inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "name": "nodes",
                     "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view",
                     "type": "function"}, {"inputs": [{"internalType": "uint256", "name": "", "type": "uint256"},
                                                      {"internalType": "uint256", "name": "receivedPayoutWei",
                                                       "type": "uint256"}], "name": "onKick", "outputs": [],
                                           "stateMutability": "nonpayable", "type": "function"},
                    {"inputs": [{"internalType": "address", "name": "targetOperator", "type": "address"}],
                     "name": "onReviewRequest", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
                    {"inputs": [{"internalType": "uint256", "name": "amountSlashed", "type": "uint256"}], "name": "onSlash",
                     "outputs": [], "stateMutability": "nonpayable", "type": "function"}, {
                        "inputs": [{"internalType": "address", "name": "sender", "type": "address"},
                                   {"internalType": "uint256", "name": "amount", "type": "uint256"},
                                   {"internalType": "bytes", "name": "data", "type": "bytes"}], "name": "onTokenTransfer",
                        "outputs": [], "stateMutability": "nonpayable", "type": "function"},
                    {"inputs": [], "name": "operatorsCutFraction",
                     "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view",
                     "type": "function"},
                    {"inputs": [], "name": "owner", "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                     "stateMutability": "view", "type": "function"}, {"inputs": [], "name": "payOutFirstInQueue",
                                                                      "outputs": [
                                                                          {"internalType": "bool", "name": "payoutComplete",
                                                                           "type": "bool"}],
                                                                      "stateMutability": "nonpayable", "type": "function"},
                    {"inputs": [{"internalType": "uint256", "name": "maxIterations", "type": "uint256"}],
                     "name": "payOutQueue", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
                    {"inputs": [], "name": "queueCurrentIndex",
                     "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view",
                     "type": "function"},
                    {"inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "name": "queueEntryAt",
                     "outputs": [{"internalType": "address", "name": "delegator", "type": "address"},
                                 {"internalType": "uint256", "name": "amountWei", "type": "uint256"},
                                 {"internalType": "uint256", "name": "timestamp", "type": "uint256"}],
                     "stateMutability": "view", "type": "function"}, {"inputs": [], "name": "queueIsEmpty", "outputs": [
            {"internalType": "bool", "name": "", "type": "bool"}], "stateMutability": "view", "type": "function"},
                    {"inputs": [], "name": "queueLastIndex",
                     "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view",
                     "type": "function"}, {"inputs": [], "name": "queueModule", "outputs": [
            {"internalType": "contract IQueueModule", "name": "", "type": "address"}], "stateMutability": "view",
                                           "type": "function"}, {
                        "inputs": [{"internalType": "contract Sponsorship", "name": "sponsorship", "type": "address"},
                                   {"internalType": "uint256", "name": "targetStakeWei", "type": "uint256"}],
                        "name": "reduceStakeTo", "outputs": [], "stateMutability": "nonpayable", "type": "function"}, {
                        "inputs": [{"internalType": "contract Sponsorship", "name": "sponsorship", "type": "address"},
                                   {"internalType": "uint256", "name": "targetStakeWei", "type": "uint256"}],
                        "name": "reduceStakeWithoutQueue", "outputs": [], "stateMutability": "nonpayable",
                        "type": "function"}, {"inputs": [{"internalType": "bytes32", "name": "role", "type": "bytes32"},
                                                         {"internalType": "address", "name": "account", "type": "address"}],
                                              "name": "renounceRole", "outputs": [], "stateMutability": "nonpayable",
                                              "type": "function"}, {
                        "inputs": [{"internalType": "bytes32", "name": "role", "type": "bytes32"},
                                   {"internalType": "address", "name": "account", "type": "address"}], "name": "revokeRole",
                        "outputs": [], "stateMutability": "nonpayable", "type": "function"}, {
                        "inputs": [{"internalType": "contract IDelegationPolicy", "name": "policy", "type": "address"},
                                   {"internalType": "uint256", "name": "param", "type": "uint256"}],
                        "name": "setDelegationPolicy", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
                    {"inputs": [{"internalType": "contract IExchangeRatePolicy", "name": "policy", "type": "address"},
                                {"internalType": "uint256", "name": "param", "type": "uint256"}],
                     "name": "setExchangeRatePolicy", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
                    {"inputs": [{"internalType": "address[]", "name": "newNodes", "type": "address[]"}],
                     "name": "setNodeAddresses", "outputs": [], "stateMutability": "nonpayable", "type": "function"}, {
                        "inputs": [{"internalType": "contract IUndelegationPolicy", "name": "policy", "type": "address"},
                                   {"internalType": "uint256", "name": "param", "type": "uint256"}],
                        "name": "setUndelegationPolicy", "outputs": [], "stateMutability": "nonpayable",
                        "type": "function"},
                    {"inputs": [{"internalType": "contract Sponsorship", "name": "", "type": "address"}],
                     "name": "slashedIn", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                     "stateMutability": "view", "type": "function"},
                    {"inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "name": "sponsorships",
                     "outputs": [{"internalType": "contract Sponsorship", "name": "", "type": "address"}],
                     "stateMutability": "view", "type": "function"}, {
                        "inputs": [{"internalType": "contract Sponsorship", "name": "sponsorship", "type": "address"},
                                   {"internalType": "uint256", "name": "amountWei", "type": "uint256"}], "name": "stake",
                        "outputs": [], "stateMutability": "nonpayable", "type": "function"},
                    {"inputs": [], "name": "stakeModule",
                     "outputs": [{"internalType": "contract IStakeModule", "name": "", "type": "address"}],
                     "stateMutability": "view", "type": "function"},
                    {"inputs": [{"internalType": "contract Sponsorship", "name": "", "type": "address"}],
                     "name": "stakedInto", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                     "stateMutability": "view", "type": "function"}, {"inputs": [], "name": "streamId", "outputs": [
            {"internalType": "string", "name": "", "type": "string"}], "stateMutability": "view", "type": "function"},
                    {"inputs": [], "name": "streamRegistry",
                     "outputs": [{"internalType": "contract IStreamRegistryV4", "name": "", "type": "address"}],
                     "stateMutability": "view", "type": "function"}, {"inputs": [], "name": "streamrConfig", "outputs": [
            {"internalType": "contract StreamrConfig", "name": "", "type": "address"}], "stateMutability": "view",
                                                                      "type": "function"},
                    {"inputs": [{"internalType": "bytes4", "name": "interfaceId", "type": "bytes4"}],
                     "name": "supportsInterface", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
                     "stateMutability": "view", "type": "function"},
                    {"inputs": [], "name": "symbol", "outputs": [{"internalType": "string", "name": "", "type": "string"}],
                     "stateMutability": "view", "type": "function"}, {"inputs": [], "name": "token", "outputs": [
            {"internalType": "contract IERC677", "name": "", "type": "address"}], "stateMutability": "view",
                                                                      "type": "function"},
                    {"inputs": [], "name": "totalSlashedInSponsorshipsWei",
                     "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view",
                     "type": "function"}, {"inputs": [], "name": "totalStakedIntoSponsorshipsWei",
                                           "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                                           "stateMutability": "view", "type": "function"},
                    {"inputs": [], "name": "totalSupply",
                     "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view",
                     "type": "function"}, {"inputs": [{"internalType": "address", "name": "to", "type": "address"},
                                                      {"internalType": "uint256", "name": "amount", "type": "uint256"}],
                                           "name": "transfer",
                                           "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
                                           "stateMutability": "nonpayable", "type": "function"}, {
                        "inputs": [{"internalType": "address", "name": "from", "type": "address"},
                                   {"internalType": "address", "name": "to", "type": "address"},
                                   {"internalType": "uint256", "name": "amount", "type": "uint256"}],
                        "name": "transferFrom", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
                        "stateMutability": "nonpayable", "type": "function"}, {
                        "inputs": [{"internalType": "contract Operator", "name": "other", "type": "address"},
                                   {"internalType": "contract Sponsorship[]", "name": "sponsorshipAddresses",
                                    "type": "address[]"}], "name": "triggerAnotherOperatorWithdraw", "outputs": [],
                        "stateMutability": "nonpayable", "type": "function"},
                    {"inputs": [{"internalType": "uint256", "name": "amountDataWei", "type": "uint256"}],
                     "name": "undelegate", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
                    {"inputs": [], "name": "undelegationPolicy",
                     "outputs": [{"internalType": "contract IUndelegationPolicy", "name": "", "type": "address"}],
                     "stateMutability": "view", "type": "function"}, {"inputs": [], "name": "undelegationQueue",
                                                                      "outputs": [{"components": [
                                                                          {"internalType": "address", "name": "delegator",
                                                                           "type": "address"},
                                                                          {"internalType": "uint256", "name": "amountWei",
                                                                           "type": "uint256"},
                                                                          {"internalType": "uint256", "name": "timestamp",
                                                                           "type": "uint256"}],
                                                                                   "internalType": "struct Operator.UndelegationQueueEntry[]",
                                                                                   "name": "queue", "type": "tuple[]"}],
                                                                      "stateMutability": "view", "type": "function"},
                    {"inputs": [{"internalType": "contract Sponsorship", "name": "sponsorship", "type": "address"}],
                     "name": "unstake", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
                    {"inputs": [{"internalType": "contract Sponsorship", "name": "sponsorship", "type": "address"}],
                     "name": "unstakeWithoutQueue", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
                    {"inputs": [{"internalType": "string", "name": "metadataJsonString", "type": "string"}],
                     "name": "updateMetadata", "outputs": [], "stateMutability": "nonpayable", "type": "function"}, {
                        "inputs": [{"internalType": "address[]", "name": "addNodes", "type": "address[]"},
                                   {"internalType": "address[]", "name": "removeNodes", "type": "address[]"}],
                        "name": "updateNodeAddresses", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
                    {"inputs": [{"internalType": "uint256", "name": "newOperatorsCutFraction", "type": "uint256"}],
                     "name": "updateOperatorsCutFraction", "outputs": [], "stateMutability": "nonpayable",
                     "type": "function"},
                    {"inputs": [{"internalType": "string", "name": "metadataJsonString", "type": "string"}],
                     "name": "updateStreamMetadata", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
                    {"inputs": [], "name": "valueWithoutEarnings",
                     "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view",
                     "type": "function"}, {
                        "inputs": [{"internalType": "contract Sponsorship", "name": "sponsorship", "type": "address"},
                                   {"internalType": "address", "name": "targetOperator", "type": "address"},
                                   {"internalType": "bytes32", "name": "voteData", "type": "bytes32"}],
                        "name": "voteOnFlag", "outputs": [], "stateMutability": "nonpayable", "type": "function"}, {
                        "inputs": [{"internalType": "contract Sponsorship[]", "name": "sponsorshipAddresses",
                                    "type": "address[]"}], "name": "withdrawEarningsFromSponsorships", "outputs": [],
                        "stateMutability": "nonpayable", "type": "function"}, {"inputs": [
            {"internalType": "contract Sponsorship[]", "name": "sponsorshipAddresses", "type": "address[]"}],
                                                                               "name": "withdrawEarningsFromSponsorshipsWithoutQueue",
                                                                               "outputs": [{"internalType": "uint256",
                                                                                            "name": "withdrawnEarningsDataWei",
                                                                                            "type": "uint256"}],
                                                                               "stateMutability": "nonpayable",
                                                                               "type": "function"}]

    contract = web3.eth.contract(address=contract_address, abi=contract_abi)
    account = web3.eth.account.from_key(wallet_private_key)
    web3.eth.defaultAccount = account.address

    if have_enough_fund(web3, account.address):
        run_harvest_process(web3=web3, cfg=cfg, contract=contract,
                            account=account, wallet_private_key=wallet_private_key)
