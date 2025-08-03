{
  description = "BeaTool Build/Run Environment";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";
  };

  outputs =
    {
      self,
      nixpkgs,
      ...
    }@inputs:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      fhs = pkgs.buildFHSEnv {
        name = "bea-tooling-env";
        targetPkgs =
          pkgs:
          (with pkgs; [
            uv
            libudev-zero
            libusb1.out
          ]);
      };
    in
    {
      devShells.${system}.default = fhs.env;
    };
}
