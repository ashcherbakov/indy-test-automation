import pytest
import asyncio
from system.utils import *
import docker
from system.docker_setup import NETWORK_NAME


@pytest.mark.usefixtures('docker_setup_and_teardown')
class TestCatchUpSuite:

    @pytest.mark.nodes_num(9)
    @pytest.mark.asyncio
    async def test_case_stopping(
            self, pool_handler, wallet_handler, get_default_trustee, nodes_num
    ):
        trustee_did, _ = get_default_trustee
        test_nodes = [NodeHost(i) for i in range(1, nodes_num+1)]
        await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)
        await ensure_pool_is_in_sync(nodes_num=nodes_num)

        test_nodes[-1].stop_service()
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=100, timeout=60)

        test_nodes[-2].stop_service()
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=75, timeout=60)

        test_nodes[-2].start_service()
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=50, timeout=60)

        test_nodes[-1].start_service()
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=25, timeout=60)

        await ensure_pool_is_in_sync(nodes_num=nodes_num)
        await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)

    @pytest.mark.nodes_num(9)
    @pytest.mark.asyncio
    async def test_case_demoting(
            self, pool_handler, wallet_handler, get_default_trustee, nodes_num
    ):
        trustee_did, _ = get_default_trustee
        pool_info = get_pool_info('1')
        print('\nPOOL INFO:\n{}'.format(pool_info))
        await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)
        await ensure_pool_is_in_sync(nodes_num=nodes_num)

        await eventually(demote_node, pool_handler, wallet_handler, trustee_did, 'Node9', pool_info['Node9'])
        await pool.refresh_pool_ledger(pool_handler)
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=100, timeout=60)

        await eventually(demote_node, pool_handler, wallet_handler, trustee_did, 'Node8', pool_info['Node8'])
        await pool.refresh_pool_ledger(pool_handler)
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=75, timeout=60)

        await eventually(promote_node, pool_handler, wallet_handler, trustee_did, 'Node8', pool_info['Node8'])
        await pool.refresh_pool_ledger(pool_handler)
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=50, timeout=60)

        await eventually(promote_node, pool_handler, wallet_handler, trustee_did, 'Node9', pool_info['Node9'])
        await pool.refresh_pool_ledger(pool_handler)
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=25, timeout=60)

        await ensure_pool_is_in_sync(nodes_num=nodes_num)
        await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)

    @pytest.mark.nodes_num(9)
    @pytest.mark.asyncio
    async def test_case_out_of_network(
            self, pool_handler, wallet_handler, get_default_trustee, nodes_num
    ):
        client = docker.from_env()
        trustee_did, _ = get_default_trustee

        # # --- update config
        # # TODO move this into new helper to update the whole pool config easily
        # test_nodes = [NodeHost(i) for i in range(1, nodes_num+1)]
        # path_to_config = '/etc/indy/indy_config.py'
        # separator = "echo ' '"
        # print(
        #     [
        #         node.run(
        #             "{} >> {} && echo 'RETRY_TIMEOUT_NOT_RESTRICTED = 6' >> {}".format(
        #                 separator, path_to_config, path_to_config
        #             )
        #         ) for node in test_nodes
        #     ]
        # )
        # print(
        #     [
        #         node.run(
        #             "{} >> {} && echo 'RETRY_TIMEOUT_RESTRICTED = 15' >> {}".format(
        #                 separator, path_to_config, path_to_config
        #             )
        #         ) for node in test_nodes
        #     ]
        # )
        # print(
        #     [
        #         node.run(
        #             "{} >> {} && echo 'MAX_RECONNECT_RETRY_ON_SAME_SOCKET = 1' >> {}".format(
        #                 separator, path_to_config, path_to_config
        #             )
        #         ) for node in test_nodes
        #     ]
        # )
        # print([node.restart_service() for node in test_nodes])
        # # ---

        await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)
        await ensure_pool_is_in_sync(nodes_num=nodes_num)

        client.networks.list(names=[NETWORK_NAME])[0].disconnect('node9')
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=100, timeout=60)

        client.networks.list(names=[NETWORK_NAME])[0].disconnect('node8')
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=75, timeout=60)

        client.networks.list(names=[NETWORK_NAME])[0].connect('node8')
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=50, timeout=60)

        client.networks.list(names=[NETWORK_NAME])[0].connect('node9')
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=25, timeout=60)

        await ensure_pool_is_in_sync(nodes_num=nodes_num)
        await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)