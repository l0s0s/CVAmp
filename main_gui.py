import sys
import traceback

def main():
    try:
        from cvamp.gui import GUI
        from cvamp.manager import InstanceManager

        SPAWNER_THREAD_COUNT = 3
        CLOSER_THREAD_COUNT = 10
        PROXY_FILE_NAME = "proxy_list.txt"
        HEADLESS = True
        AUTO_RESTART = False
        SPAWN_INTERVAL_SECONDS = 2

        manager = InstanceManager(
            spawn_thread_count=SPAWNER_THREAD_COUNT,
            delete_thread_count=CLOSER_THREAD_COUNT,
            headless=HEADLESS,
            auto_restart=AUTO_RESTART,
            proxy_file_name=PROXY_FILE_NAME,
            spawn_interval_seconds=SPAWN_INTERVAL_SECONDS,
        )

        print("Available proxies:", len(manager.proxies.proxy_list))
        print("Available window locations:", len(manager.screen.spawn_locations))

        GUI(manager).run()
    except Exception as e:
        print("\n" + "=" * 55)
        print("CRITICAL ERROR OCCURRED DURING APP STARTUP:")
        print("=" * 55)
        traceback.print_exc()
        print("=" * 55)
        print("Check cvamp.log for additional details.")
        print("=" * 55 + "\n")
        input("Press Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    main()
